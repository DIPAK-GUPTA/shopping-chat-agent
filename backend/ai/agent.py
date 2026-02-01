"""
Main AI Shopping Agent
Handles user queries using Gemini AI and phone catalog
"""
import json
import re
import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime

import google.generativeai as genai

from config import settings
from models.chat import (
    ChatRequest, ChatResponse, ChatMessage, SessionContext,
    ProductCard, ComparisonData, QueryIntent, MessageRole
)
from models.phone import Phone, PhoneFilter
from database.repository import phone_repository
from ai.prompts import (
    SYSTEM_PROMPT, INTENT_CLASSIFICATION_PROMPT, RECOMMENDATION_PROMPT,
    COMPARISON_PROMPT, EXPLANATION_PROMPT, DETAILS_PROMPT,
    ADVERSARIAL_RESPONSE, OFF_TOPIC_RESPONSE, GREETING_RESPONSE
)
from ai.safety import safety_filter


class ShoppingAgent:
    """AI Shopping Agent for mobile phones"""
    
    def __init__(self):
        """Initialize the shopping agent with Gemini"""
        self.sessions: Dict[str, SessionContext] = {}
        self._configure_gemini()
    
    def _configure_gemini(self) -> None:
        """Configure Gemini AI"""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use basic model configuration for compatibility
            self.model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL
            )
            self.system_prompt = SYSTEM_PROMPT
            # Enable LLM-based safety detection
            safety_filter.set_llm_model(self.model)
            safety_filter.llm_enabled = settings.SAFETY_LLM_ENABLED
        else:
            self.model = None
            self.system_prompt = ""
            print("Warning: GEMINI_API_KEY not set. Agent will have limited functionality.")
    
    def _get_or_create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_activity = datetime.utcnow()
            return session
        
        new_session_id = session_id or str(uuid.uuid4())
        session = SessionContext(session_id=new_session_id)
        self.sessions[new_session_id] = session
        return session
    
    def _classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify user intent using Gemini"""
        if not self.model:
            return {"intent": "SEARCH", "confidence": 0.5}
        
        try:
            prompt = INTENT_CLASSIFICATION_PROMPT.format(user_message=message)
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            text = response.text.strip()
            # Find JSON in response
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {"intent": "SEARCH", "confidence": 0.5}
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            return {"intent": "SEARCH", "confidence": 0.5}
    
    def _phone_to_card(self, phone: Phone) -> ProductCard:
        """Convert Phone model to ProductCard for frontend"""
        return ProductCard(
            id=phone.id,
            brand=phone.brand,
            model=phone.model,
            price_inr=phone.price_inr,
            display_size=phone.display_size,
            ram_gb=phone.ram_gb,
            storage_gb=phone.storage_gb,
            battery_mah=phone.battery_mah,
            camera_main_mp=phone.camera.main_mp,
            rating=phone.rating,
            image_url=phone.image_url,
            key_features=phone.special_features[:4]  # Top 4 features
        )
    
    def _format_phone_for_ai(self, phone: Phone) -> str:
        """Format phone data for AI prompt"""
        return f"""
**{phone.brand} {phone.model}** (ID: {phone.id})
- Price: ₹{phone.price_inr:,}
- Display: {phone.display_size}" {phone.display_type}, {phone.refresh_rate}Hz
- Processor: {phone.processor}
- RAM/Storage: {phone.ram_gb}GB / {phone.storage_gb}GB
- Camera: {phone.camera.main_mp}MP main, Features: {', '.join(phone.camera.features[:3])}
- Battery: {phone.battery_mah}mAh, {phone.fast_charging_watts}W charging
- Special: {', '.join(phone.special_features[:3])}
- Rating: {phone.rating}/5 ({phone.reviews_count:,} reviews)
"""
    
    def _find_phones_in_message(self, message: str) -> List[Phone]:
        """Find mentioned phones in message"""
        phones = []
        message_lower = message.lower()
        
        for phone in phone_repository.get_all():
            # Check if phone model or full name is mentioned
            if (phone.model.lower() in message_lower or 
                phone.full_name.lower() in message_lower or
                phone.id.lower() in message_lower):
                phones.append(phone)
        
        return phones
    
    def _extract_price_from_message(self, message: str) -> Optional[int]:
        """Extract price/budget from message"""
        # Patterns like "30k", "30000", "₹30,000"
        patterns = [
            r'(\d+)\s*k\b',  # 30k
            r'₹?\s*(\d{1,2}),?(\d{3})',  # ₹30,000 or 30000
            r'under\s+₹?\s*(\d+)',  # under 30000
            r'below\s+₹?\s*(\d+)',  # below 30000
            r'budget\s+(?:of\s+)?₹?\s*(\d+)',  # budget of 30000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:  # Pattern like 30,000
                    return int(groups[0] + groups[1])
                elif len(groups) == 1:
                    num = int(groups[0])
                    if num < 1000:  # Assume it's in thousands (30k)
                        return num * 1000
                    return num
        
        return None
    
    def _handle_search(self, message: str, intent_data: Dict) -> tuple[str, List[Phone]]:
        """Handle search/recommendation queries with focus-based selection"""
        # Build filter from intent data
        filters = PhoneFilter()
        
        # Handle budget extraction
        if intent_data.get("budget_max"):
            filters.max_price = int(intent_data["budget_max"])
        else:
            # Try to extract from message
            budget = self._extract_price_from_message(message)
            if budget:
                filters.max_price = budget
        
        if intent_data.get("budget_min"):
            filters.min_price = int(intent_data["budget_min"])
        
        if intent_data.get("brand"):
            filters.brand = intent_data["brand"]
        
        if intent_data.get("compact"):
            filters.compact_only = True
        
        # Get focus priority from intent
        focus = intent_data.get("focus")
        message_lower = message.lower()
        
        # Detect focus from message if not provided
        if not focus:
            if "camera" in message_lower or "photo" in message_lower:
                focus = "camera"
            elif "battery" in message_lower or "endurance" in message_lower:
                focus = "battery"
            elif "gaming" in message_lower or "game" in message_lower:
                focus = "gaming"
            elif "value" in message_lower or "budget" in message_lower or "worth" in message_lower:
                focus = "value"
            elif "compact" in message_lower or "small" in message_lower or "one hand" in message_lower:
                focus = "compact"
        
        # Get phones based on focus
        if focus == "camera":
            matching_phones = phone_repository.get_camera_phones(filters.max_price)[:5]
        elif focus == "battery":
            matching_phones = phone_repository.get_battery_champions(filters.max_price)[:5]
        elif focus == "gaming":
            matching_phones = phone_repository.get_gaming_phones(filters.max_price)[:5]
        elif focus == "compact":
            matching_phones = phone_repository.get_compact_phones(filters.max_price)[:5]
        elif focus == "value" and filters.max_price:
            min_price = filters.min_price or 0
            matching_phones = phone_repository.get_value_phones(min_price, filters.max_price)[:5]
        else:
            # Default filter-based search
            matching_phones = phone_repository.filter_phones(filters)
            
            # Check for fast charging requirement  
            if intent_data.get("fast_charging") or "fast charg" in message_lower or "quick charg" in message_lower:
                matching_phones = phone_repository.get_fast_charging_phones(filters.max_price)[:5]
        
        # Fallback if no matches
        if not matching_phones:
            matching_phones = phone_repository.filter_phones(filters)[:5]
        if not matching_phones:
            matching_phones = phone_repository.get_all()[:5]
        else:
            matching_phones = matching_phones[:5]
        
        # Generate AI response
        if self.model and matching_phones:
            try:
                phones_text = "\n".join([self._format_phone_for_ai(p) for p in matching_phones])
                
                budget_info = f"Max ₹{filters.max_price:,}" if filters.max_price else "Not specified"
                if filters.min_price:
                    budget_info = f"₹{filters.min_price:,} - ₹{filters.max_price:,}" if filters.max_price else f"Min ₹{filters.min_price:,}"
                brand_info = filters.brand or "Any"
                focus_info = focus or "General best options"
                features_info = ", ".join(intent_data.get("features", [])) or "Not specified"
                compact_info = "Yes" if filters.compact_only else "No"
                fast_charging_info = "Yes" if intent_data.get("fast_charging") else "No"
                
                prompt = RECOMMENDATION_PROMPT.format(
                    user_query=message,
                    budget_info=budget_info,
                    brand_info=brand_info,
                    focus_info=focus_info,
                    features_info=features_info,
                    compact_info=compact_info,
                    fast_charging_info=fast_charging_info,
                    matching_phones=phones_text
                )
                
                response = self.model.generate_content(prompt)
                return response.text, matching_phones
                
            except Exception as e:
                print(f"Recommendation error: {e}")
        
        # Fallback response
        if matching_phones:
            phones_list = ", ".join([p.full_name for p in matching_phones[:3]])
            return f"Based on your requirements, I recommend checking out: {phones_list}. Would you like more details about any of these?", matching_phones
        
        return "I couldn't find phones matching your exact criteria. Could you try adjusting your requirements?", []
    
    def _handle_compare(self, message: str, intent_data: Dict) -> tuple[str, Optional[ComparisonData]]:
        """Handle comparison queries"""
        # Find phones mentioned in message
        phones = self._find_phones_in_message(message)
        
        # Also check intent data for phone names
        if intent_data.get("phone_names"):
            for name in intent_data["phone_names"]:
                found = phone_repository.search(name)
                phones.extend(found)
        
        # Remove duplicates
        seen_ids = set()
        unique_phones = []
        for p in phones:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique_phones.append(p)
        
        phones = unique_phones[:3]  # Max 3 phones
        
        if len(phones) < 2:
            return "Please mention 2 or 3 specific phone models to compare. For example: 'Compare Pixel 8a vs OnePlus 12R'", None
        
        # Get comparison data
        comparison = phone_repository.compare_phones([p.id for p in phones])
        
        if self.model:
            try:
                phones_text = "\n".join([self._format_phone_for_ai(p) for p in phones])
                
                prompt = COMPARISON_PROMPT.format(
                    phones_data=phones_text,
                    user_query=message
                )
                
                response = self.model.generate_content(prompt)
                
                # Build comparison data for frontend
                comparison_data = ComparisonData(
                    phones=[self._phone_to_card(p) for p in phones],
                    comparison_table=comparison.highlights if comparison else {},
                    winner_by_category=comparison.highlights if comparison else {}
                )
                
                return response.text, comparison_data
                
            except Exception as e:
                print(f"Comparison error: {e}")
        
        # Fallback
        phones_names = " vs ".join([p.full_name for p in phones])
        return f"Comparing {phones_names}. The first phone offers better value, while the second has premium features.", None
    
    def _handle_explain(self, message: str) -> str:
        """Handle explanation queries including comparative explanations"""
        # Extended list of technical terms
        terms = [
            "OIS", "EIS", "AMOLED", "LCD", "OLED", "LTPO", "refresh rate",
            "mAh", "fast charging", "5G", "NFC", "IP68", "IP67", "Gorilla Glass",
            "telephoto", "ultra wide", "RAM", "ROM", "storage", "processor",
            "Snapdragon", "Exynos", "Dimensity", "Tensor", "Bionic",
            "HDR", "HDR10", "Dolby Vision", "stereo speakers", "LPDDR5"
        ]
        
        message_lower = message.lower()
        terms_found = []
        
        # Check for comparison pattern (X vs Y, X or Y, X and Y, difference between X and Y)
        vs_patterns = [
            r"(\w+)\s+vs\.?\s+(\w+)",
            r"(\w+)\s+or\s+(\w+)",
            r"difference\s+between\s+(\w+)\s+and\s+(\w+)",
            r"(\w+)\s+versus\s+(\w+)",
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                terms_found = [match.group(1).upper(), match.group(2).upper()]
                break
        
        # Find single term if no comparison found
        if not terms_found:
            for term in terms:
                if term.lower() in message_lower:
                    terms_found.append(term)
                    if len(terms_found) >= 2:
                        break
        
        # Try to extract from message patterns if still not found
        if not terms_found:
            patterns = [
                r"what\s+is\s+(\w+)",
                r"explain\s+(\w+)",
                r"what\s+does\s+(\w+)\s+mean",
                r"meaning\s+of\s+(\w+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    terms_found = [match.group(1)]
                    break
        
        # Format term for display
        term_display = " vs ".join(terms_found) if len(terms_found) > 1 else (terms_found[0] if terms_found else "the term")
        
        if self.model and terms_found:
            try:
                prompt = EXPLANATION_PROMPT.format(
                    term=term_display,
                    user_query=message
                )
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Explanation error: {e}")
        
        # Enhanced fallback explanations
        explanations = {
            "ois": "**OIS (Optical Image Stabilization)** physically moves the lens to counteract hand shake, resulting in sharper photos and smoother videos. It's especially helpful in low light and is the better stabilization technology.",
            "eis": "**EIS (Electronic Image Stabilization)** uses software to reduce shake by cropping and adjusting the video frame. It's less effective than OIS but adds no extra hardware cost.",
            "amoled": "**AMOLED** displays offer vibrant colors, true blacks (since pixels turn off completely), and better contrast than LCD. Great for watching videos and battery efficiency in dark mode.",
            "lcd": "**LCD (Liquid Crystal Display)** uses a backlight behind the screen. It's cheaper to produce but can't achieve true blacks like AMOLED. Good for budget phones.",
            "ltpo": "**LTPO (Low-Temperature Polycrystalline Oxide)** allows the display to dynamically adjust refresh rate (1-120Hz), saving battery while still being smooth when needed.",
            "mah": "**mAh (milliamp-hour)** measures battery capacity. Higher mAh = longer battery life. 5000mAh is typically a full day of heavy use.",
            "5g": "**5G** is the latest mobile network technology, offering faster speeds (up to 10x 4G) and lower latency. Useful for streaming, gaming, and future-proofing.",
            "ip68": "**IP68** is a dust and water resistance rating. It means the phone can survive being submerged in 1.5m of water for 30 minutes. Great for rainy conditions or accidental drops in water.",
            "ip67": "**IP67** means dust-tight and can survive 1m water submersion for 30 minutes. Slightly less protection than IP68.",
            "refresh rate": "**Refresh rate** (measured in Hz) is how many times the screen updates per second. 120Hz is buttery smooth for scrolling and gaming, while 60Hz is standard.",
            "fast charging": "**Fast charging** uses higher wattage to charge your phone quickly. 65W can charge 0-100% in ~35 mins, while 18W takes 1.5-2 hours.",
            "nfc": "**NFC (Near Field Communication)** enables contactless payments like Google Pay and Apple Pay. Essential for tap-to-pay functionality.",
        }
        
        # Handle comparison fallback
        if len(terms_found) >= 2 and terms_found[0].lower() == "ois" and terms_found[1].lower() == "eis":
            return """**OIS vs EIS - The Key Differences:**

📸 **OIS (Optical Image Stabilization)**
- Physically moves the camera lens to counteract shake
- Better image quality, especially in low light
- More effective for photos and video
- Found in mid-range to flagship phones

📱 **EIS (Electronic Image Stabilization)**  
- Software-based, crops the video to remove shake
- Slightly reduces video resolution
- No extra hardware cost
- Found in most phones including budget ones

**Verdict:** OIS is better for image quality. Look for phones with OIS if camera is your priority. Many good phones have both OIS + EIS for best results!"""
        
        # Return single term fallback
        if terms_found and terms_found[0].lower() in explanations:
            return explanations[terms_found[0].lower()]
        
        return "I'd be happy to explain that! Could you please specify which term you'd like me to explain? For example: 'What is OIS?' or 'Explain the difference between AMOLED and LCD'"
    
    def _handle_details(self, message: str, session: SessionContext, intent_data: Dict = None) -> tuple[str, List[Phone]]:
        """Handle details/more info queries with better context awareness"""
        intent_data = intent_data or {}
        message_lower = message.lower()
        
        # Find phone mentioned directly
        phones = self._find_phones_in_message(message)
        
        # Check for position references like "first one", "the second", etc.
        if not phones and session.last_mentioned_phones:
            position_patterns = [
                (r"\b(first|1st)\b", 0),
                (r"\b(second|2nd)\b", 1),
                (r"\b(third|3rd)\b", 2),
                (r"\b(this|that|it)\s+(one|phone)?\b", 0),
                (r"\bi\s+like\s+(this|that|it)\b", 0),
                (r"\btell\s+me\s+more\b", 0),
                (r"\bmore\s+details?\b", 0),
            ]
            
            for pattern, idx in position_patterns:
                if re.search(pattern, message_lower):
                    if idx < len(session.last_mentioned_phones):
                        phones = phone_repository.get_by_ids([session.last_mentioned_phones[idx]])
                        break
        
        # Check if intent_data indicates context wanted
        if not phones and intent_data.get("wants_context") and session.last_mentioned_phones:
            phones = phone_repository.get_by_ids(session.last_mentioned_phones[:1])
        
        # Final fallback to most recent phone
        if not phones and session.last_mentioned_phones:
            phones = phone_repository.get_by_ids(session.last_mentioned_phones[:1])
        
        if not phones:
            return "Which phone would you like to know more about? Please mention the specific model, or ask about one of the phones I just recommended.", []
        
        phone = phones[0]
        
        if self.model:
            try:
                prompt = DETAILS_PROMPT.format(
                    phone_data=self._format_phone_for_ai(phone),
                    user_query=message
                )
                response = self.model.generate_content(prompt)
                return response.text, [phone]
            except Exception as e:
                print(f"Details error: {e}")
        
        # Fallback
        details = f"""Here are the details for **{phone.full_name}**:

**Price:** ₹{phone.price_inr:,}
**Display:** {phone.display_size}" {phone.display_type} at {phone.refresh_rate}Hz
**Performance:** {phone.processor}, {phone.ram_gb}GB RAM, {phone.storage_gb}GB storage
**Camera:** {phone.camera.main_mp}MP main camera with {', '.join(phone.camera.features[:3])}
**Battery:** {phone.battery_mah}mAh with {phone.fast_charging_watts}W fast charging
**Special Features:** {', '.join(phone.special_features[:4])}
**Rating:** {phone.rating}/5 from {phone.reviews_count:,} reviews

Would you like me to compare this with another phone?"""
        
        return details, [phone]
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """Process user message and generate response"""
        session = self._get_or_create_session(request.session_id)
        
        # Add user message to history
        user_message = ChatMessage(
            role=MessageRole.USER,
            content=request.message
        )
        session.messages.append(user_message)
        
        # Safety check first
        safety_intent, safety_reason = safety_filter.analyze(request.message)
        
        if safety_intent == QueryIntent.ADVERSARIAL:
            response_text = ADVERSARIAL_RESPONSE
            return ChatResponse(
                message=response_text,
                intent=QueryIntent.ADVERSARIAL,
                session_id=session.session_id,
                is_refusal=True
            )
        
        if safety_intent == QueryIntent.OFF_TOPIC:
            response_text = OFF_TOPIC_RESPONSE
            return ChatResponse(
                message=response_text,
                intent=QueryIntent.OFF_TOPIC,
                session_id=session.session_id,
                is_refusal=True
            )
        
        # Classify intent
        intent_data = self._classify_intent(request.message)
        intent_str = intent_data.get("intent", "SEARCH").upper()
        
        try:
            intent = QueryIntent(intent_str.lower())
        except ValueError:
            intent = QueryIntent.SEARCH
        
        # Handle based on intent
        products = None
        comparison = None
        phone_list = []
        
        if intent == QueryIntent.GREETING:
            response_text = GREETING_RESPONSE
        
        elif intent == QueryIntent.COMPARE:
            response_text, comparison = self._handle_compare(request.message, intent_data)
            if comparison:
                products = comparison.phones
        
        elif intent == QueryIntent.EXPLAIN:
            response_text = self._handle_explain(request.message)
        
        elif intent == QueryIntent.DETAILS:
            response_text, phone_list = self._handle_details(request.message, session, intent_data)
            if phone_list:
                products = [self._phone_to_card(p) for p in phone_list]
        
        elif intent in [QueryIntent.SEARCH, QueryIntent.RECOMMEND, QueryIntent.FILTER]:
            response_text, phone_list = self._handle_search(request.message, intent_data)
            if phone_list:
                products = [self._phone_to_card(p) for p in phone_list]
        
        else:
            response_text, phone_list = self._handle_search(request.message, intent_data)
            if phone_list:
                products = [self._phone_to_card(p) for p in phone_list]
        
        # Update session
        if phone_list:
            session.last_mentioned_phones = [p.id for p in phone_list[:3]]
        
        # Sanitize output
        response_text = safety_filter.sanitize_output(response_text)
        
        # Add assistant message to history
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response_text,
            intent=intent,
            phone_ids=session.last_mentioned_phones
        )
        session.messages.append(assistant_message)
        
        return ChatResponse(
            message=response_text,
            intent=intent,
            session_id=session.session_id,
            products=products,
            comparison=comparison,
            sources=session.last_mentioned_phones
        )


# Global agent instance
shopping_agent = ShoppingAgent()
