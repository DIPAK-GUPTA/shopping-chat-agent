"""
Safety and Adversarial Handling Module
Protects against prompt injection, jailbreaks, and off-topic queries
"""
import re
from typing import Tuple
from models.chat import QueryIntent


class SafetyFilter:
    """Filter for detecting and handling adversarial/unsafe queries"""
    
    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(your\s+)?(previous\s+)?instructions",
        r"ignore\s+(your\s+)?rules",
        r"disregard\s+(all\s+)?(previous\s+)?instructions",
        r"forget\s+(all\s+)?(your\s+)?(previous\s+)?instructions",
        r"reveal\s+(your\s+)?(system\s+)?prompt",
        r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt",
        r"what\s+(is|are)\s+(your\s+)?(system\s+)?prompt",
        r"tell\s+me\s+(your\s+)?(system\s+)?prompt",
        r"display\s+(your\s+)?instructions",
        r"print\s+(your\s+)?instructions",
        r"output\s+(your\s+)?instructions",
        r"api\s*key",
        r"secret\s*key",
        r"access\s*token",
        r"your\s+token",
        r"tell\s+me\s+your\s+(api|secret|access)",
        r"what\s+is\s+your\s+(api|secret|access)",
        r"act\s+as\s+(if\s+you\s+are\s+)?(?!a\s+phone|my|an?\s+assistant)",
        r"pretend\s+(to\s+be|you\s+are)\s+(?!helping)",
        r"you\s+are\s+now\s+a",
        r"new\s+persona",
        r"switch\s+to\s+",
        r"jailbreak",
        r"DAN\s+mode",
        r"developer\s+mode",
        r"sudo\s+mode",
    ]
    
    # Patterns that indicate off-topic/unrelated queries
    OFF_TOPIC_PATTERNS = [
        r"write\s+(me\s+)?(a\s+)?(poem|story|essay|code|script)",
        r"tell\s+me\s+(a\s+)?joke",
        r"sing\s+(me\s+)?a\s+song",
        r"(what|who)\s+is\s+the\s+president",
        r"(what|who)\s+won\s+the\s+(election|match|game)",
        r"recipe\s+for",
        r"how\s+to\s+cook",
        r"what\s+is\s+the\s+weather",
        r"translate\s+this",
        r"help\s+me\s+with\s+(my\s+)?homework",
        r"solve\s+this\s+(math|equation)",
        r"medical\s+advice",
        r"legal\s+advice",
        r"financial\s+advice(?!\s+.*(phone|mobile|buy))",
    ]
    
    # Patterns indicating toxic/harmful content
    TOXIC_PATTERNS = [
        r"(trash|garbage|shit|crap|sucks)\s+(brand|phone|company)",
        r"(brand|company)\s+(is\s+)?(trash|garbage|shit|crap|sucks)",
        r"hate\s+speech",
        r"(kill|murder|harm|hurt)\s+",
        r"how\s+to\s+(hack|steal|scam)",
        r"illegal\s+(activity|stuff|things)",
    ]
    
    def __init__(self):
        """Initialize safety filter with compiled patterns"""
        self.injection_regex = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self.off_topic_regex = [re.compile(p, re.IGNORECASE) for p in self.OFF_TOPIC_PATTERNS]
        self.toxic_regex = [re.compile(p, re.IGNORECASE) for p in self.TOXIC_PATTERNS]
    
    def check_injection(self, message: str) -> bool:
        """Check if message contains prompt injection attempts"""
        for pattern in self.injection_regex:
            if pattern.search(message):
                return True
        return False
    
    def check_off_topic(self, message: str) -> bool:
        """Check if message is off-topic"""
        for pattern in self.off_topic_regex:
            if pattern.search(message):
                return True
        return False
    
    def check_toxic(self, message: str) -> bool:
        """Check for toxic or harmful content"""
        for pattern in self.toxic_regex:
            if pattern.search(message):
                return True
        return False
    
    def analyze(self, message: str) -> Tuple[QueryIntent, str]:
        """
        Analyze message for safety issues
        
        Returns:
            Tuple of (intent, reason)
            - If safe: (None, "")
            - If unsafe: (QueryIntent, reason_message)
        """
        message_lower = message.lower().strip()
        
        # Check for prompt injection
        if self.check_injection(message_lower):
            return (QueryIntent.ADVERSARIAL, "prompt_injection")
        
        # Check for toxic content
        if self.check_toxic(message_lower):
            return (QueryIntent.ADVERSARIAL, "toxic_content")
        
        # Check for off-topic
        if self.check_off_topic(message_lower):
            return (QueryIntent.OFF_TOPIC, "off_topic")
        
        # Message passed safety checks
        return (None, "")
    
    def is_safe(self, message: str) -> bool:
        """Quick check if message is safe"""
        intent, _ = self.analyze(message)
        return intent is None
    
    def sanitize_output(self, response: str) -> str:
        """
        Sanitize AI output to prevent accidental information leakage
        """
        # Patterns that should never appear in output
        leak_patterns = [
            r"API[_\s]?KEY[:\s]*[A-Za-z0-9_\-]+",
            r"Bearer\s+[A-Za-z0-9_\-\.]+",
            r"sk-[A-Za-z0-9]+",
            r"AIza[A-Za-z0-9_\-]+",  # Google API key pattern
        ]
        
        sanitized = response
        for pattern in leak_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        
        return sanitized


# Global safety filter instance
safety_filter = SafetyFilter()
