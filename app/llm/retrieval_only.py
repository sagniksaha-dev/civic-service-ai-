import re
from typing import Any, Dict, List, Optional, Tuple
from app.llm.base import BaseLLMProvider


class RetrievalOnlyProvider(BaseLLMProvider):
    """
    Intelligent Grounded Synthesizer that compiles structured, highly accurate,
    and domain-consistent civic answers strictly from retrieved document snippets.
    Guarantees 100% offline usability without requiring external API keys.
    """

    NO_ANSWER_RESPONSE = (
        "I could not find information regarding this question in the approved civic service documents. "
        "Please check the respective department office or submit a formal inquiry."
    )

    OUT_OF_SCOPE_TERMS = {
        "spaceship", "interstellar", "mars", "alien", "crypto", "bitcoin",
        "spacecraft", "galaxy", "astrology", "superhero", "jupiter", "starship",
        "moon base", "time travel", "multiverse", "joke", "movie", "song", "actor",
        "cricket", "football", "recipe", "pasta", "biryani", "weather"
    }

    def generate_grounded_response(
        self,
        question: str,
        context_snippets: List[Dict[str, Any]],
        system_prompt: str
    ) -> Tuple[str, bool]:
        """Generate a structured, grounded answer from retrieved context snippets."""
        if not context_snippets:
            return self.NO_ANSWER_RESPONSE, False

        q_lower = question.lower().strip()
        q_words = set(re.findall(r"\w+", q_lower))

        # Check for out-of-scope rejection
        if any(term in q_words for term in self.OUT_OF_SCOPE_TERMS):
            return self.NO_ANSWER_RESPONSE, False

        # Detect primary topic / domain
        topic_info = self._detect_topic(q_lower, q_words)

        # If general inquiry, enforce strict relevance gating
        filtered_snippets = context_snippets
        if topic_info.get("domain") == "general":
            stop_words = {
                "what", "is", "the", "are", "for", "how", "to", "apply", "do", "i", "a", "an",
                "in", "of", "and", "can", "get", "need", "my", "on", "from", "with", "where",
                "tell", "me", "about", "please", "give", "you", "your", "this", "that", "which",
                "so", "jao", "kya", "hai", "ki", "ka", "ke", "ko", "se", "me", "mein", "par",
                "karo", "karna", "bolo", "boliye", "batao", "bataiye", "it", "be", "or", "as",
                "hi", "hello", "hey", "good", "night", "morning", "bye", "who", "when", "why"
            }
            meaningful_terms = {w for w in q_words if len(w) > 2 and w not in stop_words}
            if not meaningful_terms:
                return self.NO_ANSWER_RESPONSE, False

            matching_snippets = []
            for s in context_snippets:
                text_words = set(re.findall(r"\w+", s.get("text", "").lower()))
                title_words = set(re.findall(r"\w+", s.get("metadata", {}).get("title", "").lower()))
                overlap = meaningful_terms.intersection(text_words.union(title_words))
                if overlap:
                    matching_snippets.append((len(overlap), s))

            if not matching_snippets:
                return self.NO_ANSWER_RESPONSE, False

            matching_snippets.sort(key=lambda x: x[0], reverse=True)
            filtered_snippets = [item[1] for item in matching_snippets]
        else:
            filtered_snippets = self._filter_snippets(context_snippets, topic_info)
            if not filtered_snippets:
                filtered_snippets = context_snippets

        # Parse structured sections across matching snippets
        doc_structure = self._parse_document_structures(filtered_snippets, topic_info)

        # Determine user intent
        intent = self._detect_intent(q_lower)

        # Detect preferred language from system prompt or text
        lang = "en"
        if "bengali" in system_prompt.lower() or "বাংলা" in system_prompt or any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in question):
            lang = "bn"
        elif "hindi" in system_prompt.lower() or "हिंदी" in system_prompt or any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in question):
            lang = "hi"

        # Synthesize answer
        compiled_answer = self._synthesize_answer(doc_structure, topic_info, intent, lang, question)
        if not compiled_answer:
            return self.NO_ANSWER_RESPONSE, False

        return compiled_answer, True

    def _detect_topic(self, q_lower: str, q_words: set) -> Dict[str, Any]:
        """Identify the primary civic domain and specific sub-service."""
        if "birth" in q_lower or "born" in q_lower or "jonmo" in q_lower or "janma" in q_lower or "জন্ম" in q_lower or "जन्म" in q_lower:
            return {
                "domain": "birth",
                "title": "Birth Certificate Registration & Issuance",
                "dept_code": "CIV-REG",
                "dept_name": "Department of Vital Statistics & Civil Registration",
                "sub_filter": "birth"
            }
        if "death" in q_lower or "deceased" in q_lower or "crematorium" in q_lower or "burial" in q_lower or "mrityu" in q_lower or "মৃত্যু" in q_lower or "मृत्यु" in q_lower:
            return {
                "domain": "death",
                "title": "Death Certificate Registration & Issuance",
                "dept_code": "CIV-REG",
                "dept_name": "Department of Vital Statistics & Civil Registration",
                "sub_filter": "death"
            }
        if "trade" in q_lower or "business license" in q_lower or "shop license" in q_lower or "ট্রেড লাইসেন্স" in q_lower or "ट्रेड लाइसेंस" in q_lower:
            return {
                "domain": "trade",
                "title": "Commercial Trade License Issuance & Renewal",
                "dept_code": "TRADE",
                "dept_name": "Commerce & Trade Licensing Authority",
                "sub_filter": "trade"
            }
        if "water" in q_lower or "pipeline" in q_lower or "tap" in q_lower or "জল" in q_lower or "পানি" in q_lower or "पानी" in q_lower:
            return {
                "domain": "water",
                "title": "Domestic & Commercial Water Connection",
                "dept_code": "UWSD",
                "dept_name": "Urban Water Supply Department (UWSD)",
                "sub_filter": "water"
            }
        if "property tax" in q_lower or ("tax" in q_lower and ("property" in q_lower or "rebate" in q_lower or "assessment" in q_lower or "mutation" in q_lower or "কর" in q_lower or "टैक्स" in q_lower)):
            return {
                "domain": "property_tax",
                "title": "Property Tax Assessment & Annual Rebate",
                "dept_code": "REV",
                "dept_name": "Municipal Revenue & Property Administration Department",
                "sub_filter": "tax"
            }
        if "building" in q_lower or "construction" in q_lower or "architect" in q_lower or "sanction" in q_lower or "বিল্ডিং" in q_lower or "इमारत" in q_lower or "नक्शा" in q_lower:
            return {
                "domain": "building",
                "title": "Building Plan Sanction & Construction Permit",
                "dept_code": "URB-PLAN",
                "dept_name": "Department of Urban Planning & Infrastructure",
                "sub_filter": "building"
            }
        if "fire" in q_lower or "extinguisher" in q_lower or "আগুন" in q_lower or "अग्नि" in q_lower:
            return {
                "domain": "fire",
                "title": "Fire Safety NOC & Inspection Charter",
                "dept_code": "FIRE-EMERG",
                "dept_name": "Fire Safety & Disaster Management Authority",
                "sub_filter": "fire"
            }
        if "food" in q_lower or "hygiene" in q_lower or "fssai" in q_lower or "খাদ্য" in q_lower or "खाद्य" in q_lower:
            return {
                "domain": "food",
                "title": "Food Hygiene Rating & Safety Certification",
                "dept_code": "DPH-FOOD",
                "dept_name": "Department of Public Health & Food Safety",
                "sub_filter": "food"
            }
        if "waste" in q_lower or "garbage" in q_lower or "sanitation" in q_lower or "বর্জ্য" in q_lower or "कचरा" in q_lower:
            return {
                "domain": "sanitation",
                "title": "Solid Waste Management & Public Sanitation",
                "dept_code": "DPS-SAN",
                "dept_name": "Department of Public Sanitation",
                "sub_filter": "sanitation"
            }
        if "tree" in q_lower or "greenery" in q_lower or "pruning" in q_lower or "গাছ" in q_lower or "पेड़" in q_lower:
            return {
                "domain": "greenery",
                "title": "Urban Greenery & Dangerous Tree Trimming",
                "dept_code": "ENV-PARKS",
                "dept_name": "Department of Environment & Urban Greenery",
                "sub_filter": "greenery"
            }
        if "road digging" in q_lower or "trenching" in q_lower or "traffic" in q_lower or "parking" in q_lower:
            return {
                "domain": "traffic",
                "title": "Road Digging NOC & Utility Trenching Permit",
                "dept_code": "MUNI-TRANS",
                "dept_name": "Municipal Transport & Traffic Management Authority",
                "sub_filter": "traffic"
            }
        if "grievance" in q_lower or "complaint" in q_lower or "অভিযোগ" in q_lower or "शिकायत" in q_lower:
            return {
                "domain": "grievance",
                "title": "Public Grievance Redressal Mechanism",
                "dept_code": "UWSD",
                "dept_name": "Central Civic Grievance Cell",
                "sub_filter": "grievance"
            }

        return {
            "domain": "general",
            "title": "Municipal Civic Guidelines",
            "dept_code": "CIVIC",
            "dept_name": "Municipal Administration",
            "sub_filter": None
        }

    def _filter_snippets(self, snippets: List[Dict[str, Any]], topic_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Exclude cross-domain snippets that contaminate the answer."""
        domain = topic_info.get("domain")
        if domain == "general":
            return snippets

        domain_keywords = {
            "birth": ["birth", "vital statistics", "civil registration", "hospital discharge", "marriage certificate", "sdm", "sub-divisional"],
            "death": ["death", "vital statistics", "civil registration", "crematorium", "burial", "cause of death"],
            "trade": ["trade license", "commerce", "renewal", "annual renewal", "food and beverage outlets", "surcharge"],
            "water": ["water supply", "pipeline", "domestic water", "connection fee", "meter", "plumbing"],
            "property_tax": ["property tax", "revenue", "rebate", "assessment", "mutation", "interest per month", "june 30"],
            "building": ["building plan", "sanction", "architect", "structural", "far", "setback", "urban planning"],
            "fire": ["fire safety", "fire noc", "disaster management", "emergency exits", "fire extinguisher"],
            "food": ["food safety", "food hygiene", "fssai", "public health", "clean water test"],
            "sanitation": ["solid waste", "public sanitation", "garbage", "commercial waste"],
            "greenery": ["urban greenery", "tree pruning", "environment & parks", "arboriculture"],
            "traffic": ["transport", "traffic", "road digging", "trenching", "parking"],
            "grievance": ["grievance", "complaint", "redressal", "sop"]
        }

        target_kws = domain_keywords.get(domain, [])
        scored = []
        for s in snippets:
            text = s.get("text", "").lower()
            title = s.get("metadata", {}).get("title", "").lower()
            score = sum(1 for kw in target_kws if kw in text or kw in title)
            # Penalize conflicting cross-domain keywords
            if domain == "birth" and ("trade license" in text or "building plan" in text or "fire safety" in text or "water supply" in text):
                score -= 3
            elif domain == "death" and ("trade license" in text or "building plan" in text or "water supply" in text):
                score -= 3
            elif domain == "trade" and ("birth & death" in text or "water connection" in text):
                score -= 2
            elif domain == "water" and ("trade license" in text or "birth" in text):
                score -= 2
            elif domain == "property_tax" and ("trade license" in text or "water connection" in text):
                score -= 2

            if score > 0:
                scored.append((score, s))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return [item[1] for item in scored]

        return snippets

    def _detect_intent(self, q_lower: str) -> str:
        """Determine what aspect of the service the citizen is inquiring about."""
        if any(w in q_lower for w in ["document", "documents", "paper", "papers", "proof", "attach", "attachment", "dhoron", "kagoj", "নথি", "কাগজ", "दस्तावेज़", "कागजात"]):
            return "documents"
        if any(w in q_lower for w in ["fee", "fees", "cost", "charge", "charges", "price", "rebate", "penalty", "taka", "rupee", "টাকা", "ফি", "फीस", "लागत", "शुल्क"]):
            return "fees"
        if any(w in q_lower for w in ["timeline", "time", "days", "sla", "duration", "how long", "period", "due date", "সময়", "দিন", "समय", "दिन"]):
            return "timeline"
        if any(w in q_lower for w in ["how to apply", "procedure", "process", "steps", "where to apply", "method", "কীভাবে", "আবেদন", "आवेदन", "प्रक्रिया"]):
            return "procedure"
        return "overview"

    def _clean_markdown_line(self, line: str) -> str:
        """Clean leading bullet points and normalize markdown asterisks."""
        cleaned = re.sub(r"^[\s\-*•\d.)]+\s*", "", line).strip()
        # Fix unbalanced asterisks like `Birth Registration:**` -> `**Birth Registration:**`
        if cleaned.count("**") % 2 != 0:
            if cleaned.endswith(":**"):
                cleaned = "**" + cleaned
            elif ":**" in cleaned and not cleaned.startswith("**"):
                cleaned = "**" + cleaned
            else:
                cleaned = cleaned.replace("**", "")
        return cleaned

    def _parse_document_structures(self, snippets: List[Dict[str, Any]], topic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse snippet contents into structured categories."""
        structure = {
            "scope": [],
            "eligibility": [],
            "documents": [],
            "fees_sla": [],
            "procedure_redressal": [],
            "general_points": []
        }

        sub_filter = topic_info.get("sub_filter")
        seen_lines = set()

        for s in snippets:
            text = s.get("text", "")
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            current_section = "general_points"

            skip_block = False

            for line in lines:
                line_lower = line.lower()
                # Check markdown headers
                if line.startswith("#") or line.startswith("Section"):
                    cleaned_header = line.lstrip("#").strip().lower()
                    if "scope" in cleaned_header or "overview" in cleaned_header or "regulatory" in cleaned_header:
                        current_section = "scope"
                        skip_block = False
                    elif "eligibility" in cleaned_header or "application period" in cleaned_header:
                        current_section = "eligibility"
                        skip_block = False
                    elif "document" in cleaned_header or "requirement" in cleaned_header or "clearance" in cleaned_header:
                        current_section = "documents"
                        skip_block = False
                    elif "fee" in cleaned_header or "timeline" in cleaned_header or "calculation" in cleaned_header or "due date" in cleaned_header or "validity" in cleaned_header or "renewal" in cleaned_header:
                        current_section = "fees_sla"
                        skip_block = False
                    elif "grievance" in cleaned_header or "redressal" in cleaned_header or "disclaimer" in cleaned_header or "inspection" in cleaned_header:
                        current_section = "procedure_redressal"
                        skip_block = False
                    continue

                # Filter sub-sections (e.g. Birth vs Death)
                if "for birth registration:" in line_lower:
                    if sub_filter == "death":
                        skip_block = True
                        continue
                    else:
                        skip_block = False
                        current_section = "documents"
                        continue
                elif "for death registration:" in line_lower:
                    if sub_filter == "birth":
                        skip_block = True
                        continue
                    else:
                        skip_block = False
                        current_section = "documents"
                        continue

                if skip_block:
                    continue

                # Filter specific lines inside bullet lists
                if sub_filter == "birth" and ("death registration" in line_lower or "cause of death" in line_lower or "crematorium" in line_lower):
                    continue
                if sub_filter == "death" and ("birth registration" in line_lower or "hospital discharge" in line_lower):
                    continue

                cleaned = self._clean_markdown_line(line)
                if len(cleaned) < 5 or cleaned.lower() in seen_lines:
                    continue

                seen_lines.add(cleaned.lower())
                structure[current_section].append(cleaned)

        return structure

    def _synthesize_answer(
        self,
        struct: Dict[str, Any],
        topic_info: Dict[str, Any],
        intent: str,
        lang: str,
        question: str
    ) -> str:
        """Synthesize a structured and comprehensive response based on parsed information and intent."""
        domain = topic_info.get("domain", "general")
        title = topic_info.get("title", "Civic Guidelines")
        dept_code = topic_info.get("dept_code", "CIVIC")
        dept_name = topic_info.get("dept_name", "Municipal Administration")

        # If general domain without specific domain match, reject synthesis
        if domain == "general":
            return ""

        scope_lines = struct.get("scope", [])
        elig_lines = struct.get("eligibility", [])
        doc_lines = struct.get("documents", [])
        fees_lines = struct.get("fees_sla", [])
        proc_lines = struct.get("procedure_redressal", [])
        gen_lines = struct.get("general_points", [])

        if not (scope_lines or elig_lines or doc_lines or fees_lines or gen_lines):
            return ""

        # Language strings
        if lang == "bn":
            header_intro = f"অনুমোদিত পৌর নির্দেশিকা অনুসারে **{title}** (`{dept_code}`) সম্পর্কিত তথ্যাবলী:"
            sec_overview = "🏛️ পরিধি ও উদ্দেশ্য (Overview & Scope)"
            sec_eligibility = "⏱️ যোগ্যতা ও সময়সীমা (Eligibility & Timelines)"
            sec_docs = "📋 প্রয়োজনীয় নথিপত্র (Mandatory Documents Required)"
            sec_fees = "💳 প্রসেসিং ফি এবং সরকারি এসএলএ (Fees & Processing SLA)"
            sec_apply = "📝 আবেদন পদ্ধতি ও অভিযোগ নিষ্পত্তি (Application & Grievances)"
            dept_label = f"পরিচালনাকারী দপ্তর: **{dept_name}** (`{dept_code}`)"
            apply_hint = f"অনলাইনে আবেদন করতে সার্ভিস ক্যাটালগ বা ওয়ার্ড অফিসে যোগাযোগ করুন। সংশোধনের জন্য `{dept_code}` বিভাগে অভিযোগ দাখিল করা যাবে।"
        elif lang == "hi":
            header_intro = f"स्वीकृत नागरिक दिशानिर्देशों के अनुसार **{title}** (`{dept_code}`) का विवरण:"
            sec_overview = "🏛️ सेवा का विवरण (Overview & Scope)"
            sec_eligibility = "⏱️ पात्रता एवं वैधानिक समय-सीमा (Eligibility & Timelines)"
            sec_docs = "📋 आवश्यक दस्तावेज़ (Mandatory Documents Required)"
            sec_fees = "💳 प्रसंस्करण शुल्क एवं समय-सीमा (Fees & Processing SLA)"
            sec_apply = "📝 आवेदन प्रक्रिया एवं शिकायत निवारण (Application & Grievances)"
            dept_label = f"संबंधित विभाग: **{dept_name}** (`{dept_code}`)"
            apply_hint = f"पोर्टल के सर्विस कैटलॉग अथवा वार्ड कार्यालय के माध्यम से आवेदन करें। संशोधन के लिए विभाग कोड `{dept_code}` के तहत शिकायत दर्ज करें।"
        else:
            header_intro = f"According to the approved municipal civic guidelines for **{title}** (`{dept_code}`):"
            sec_overview = "🏛️ Service Overview & Scope"
            sec_eligibility = "⏱️ Eligibility & Statutory Reporting Period"
            sec_docs = "📋 Mandatory Documents Required"
            sec_fees = "💳 Processing Fees & SLA Timelines"
            sec_apply = "📝 Application Procedure & Grievance Redressal"
            dept_label = f"Responsible Authority: **{dept_name}** (`{dept_code}`)"
            apply_hint = f"Submit your application through the portal's **Service Catalogue** or at your local municipal ward office. If corrections are required, submit a grievance citing department code `{dept_code}`."

        sections_output = [header_intro, f"*{dept_label}*\n"]

        # If user specifically asked for Documents
        if intent == "documents" and doc_lines:
            sections_output.append(f"### {sec_docs}")
            for line in doc_lines:
                sections_output.append(f"- {line}")
            sections_output.append("")
            if elig_lines:
                sections_output.append(f"### {sec_eligibility}")
                for line in elig_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")
            if fees_lines:
                sections_output.append(f"### {sec_fees}")
                for line in fees_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")

        # If user specifically asked for Fees / Timeline
        elif intent in ["fees", "timeline"] and (fees_lines or elig_lines):
            if fees_lines:
                sections_output.append(f"### {sec_fees}")
                for line in fees_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")
            if elig_lines:
                sections_output.append(f"### {sec_eligibility}")
                for line in elig_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")
            if doc_lines:
                sections_output.append(f"### {sec_docs}")
                for line in doc_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")

        # General / Overview Intent
        else:
            if scope_lines:
                sections_output.append(f"### {sec_overview}")
                for line in scope_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")
            elif gen_lines:
                sections_output.append(f"### {sec_overview}")
                for line in gen_lines[:2]:
                    sections_output.append(f"- {line}")
                sections_output.append("")

            if elig_lines:
                sections_output.append(f"### {sec_eligibility}")
                for line in elig_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")

            if doc_lines:
                sections_output.append(f"### {sec_docs}")
                for line in doc_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")

            if fees_lines:
                sections_output.append(f"### {sec_fees}")
                for line in fees_lines:
                    sections_output.append(f"- {line}")
                sections_output.append("")

        # Always include procedure / redressal footer
        sections_output.append(f"### {sec_apply}")
        if proc_lines:
            for line in proc_lines:
                sections_output.append(f"- {line}")
        sections_output.append(f"- {apply_hint}")

        return "\n".join(sections_output)
