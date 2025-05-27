"""
Summarization prompts for LinkedIn Presence Automation Application.

Contains prompt templates and builders for content summarization with
tone matching and LinkedIn-specific optimization.
"""

from typing import Dict, Any, Optional
from app.schemas.ai_schemas import ToneProfile


class SummarizationPrompts:
    """
    Prompt templates and builders for content summarization.
    
    Provides structured prompts for summarizing content with user tone matching
    and LinkedIn audience optimization.
    """
    
    def __init__(self):
        """Initialize summarization prompts."""
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for summarization."""
        return """You are an expert content summarizer specializing in LinkedIn professional content.

Your role is to:
1. Extract key insights and main points from content
2. Create concise, engaging summaries optimized for LinkedIn audiences
3. Match the user's communication style and tone preferences
4. Focus on professional value and actionable insights
5. Maintain accuracy while making content more accessible

Guidelines:
- Keep summaries between 150-200 words unless specified otherwise
- Use professional language appropriate for LinkedIn
- Extract 3-5 key points that provide the most value
- Focus on insights that would interest a professional audience
- Maintain the original meaning and context
- Avoid jargon unless it's industry-standard terminology
- Structure content for easy readability

Output Format:
Provide your response as a JSON object with:
{
  "summary": "The main summary text",
  "key_points": ["Point 1", "Point 2", "Point 3"]
}"""
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for summarization."""
        return self.system_prompt
    
    def build_summarization_prompt(
        self,
        content: str,
        tone_profile: ToneProfile,
        max_length: int = 200
    ) -> str:
        """
        Build summarization prompt with user tone matching.
        
        Args:
            content: Content to summarize
            tone_profile: User's tone profile for style matching
            max_length: Maximum summary length
            
        Returns:
            Formatted summarization prompt
        """
        # Build tone context
        tone_context = self._build_tone_context(tone_profile)
        
        # Build content context
        content_length = len(content)
        content_preview = content[:500] + "..." if content_length > 500 else content
        
        prompt = f"""Please summarize the following content for a LinkedIn audience.

CONTENT TO SUMMARIZE:
{content}

USER TONE PROFILE:
{tone_context}

REQUIREMENTS:
- Maximum summary length: {max_length} words
- Extract 3-5 key points that provide professional value
- Match the user's communication style described above
- Focus on insights relevant to LinkedIn professionals
- Ensure the summary is engaging and actionable

Please provide a summary that captures the essence of the content while matching the user's professional communication style."""
        
        return prompt
    
    def build_industry_specific_prompt(
        self,
        content: str,
        tone_profile: ToneProfile,
        industry: str,
        max_length: int = 200
    ) -> str:
        """
        Build industry-specific summarization prompt.
        
        Args:
            content: Content to summarize
            tone_profile: User's tone profile
            industry: Target industry for optimization
            max_length: Maximum summary length
            
        Returns:
            Industry-optimized summarization prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        industry_context = self._get_industry_context(industry)
        
        prompt = f"""Please summarize the following content for LinkedIn professionals in the {industry} industry.

CONTENT TO SUMMARIZE:
{content}

USER TONE PROFILE:
{tone_context}

INDUSTRY CONTEXT:
{industry_context}

REQUIREMENTS:
- Maximum summary length: {max_length} words
- Focus on insights most relevant to {industry} professionals
- Use industry-appropriate terminology and examples
- Extract key points that would resonate with this audience
- Match the user's communication style
- Highlight actionable insights and trends

Please provide a summary optimized for {industry} professionals on LinkedIn."""
        
        return prompt
    
    def build_multi_focus_prompt(
        self,
        content: str,
        tone_profile: ToneProfile,
        focus_areas: list,
        max_length: int = 200
    ) -> str:
        """
        Build summarization prompt with multiple focus areas.
        
        Args:
            content: Content to summarize
            tone_profile: User's tone profile
            focus_areas: List of areas to focus on
            max_length: Maximum summary length
            
        Returns:
            Multi-focus summarization prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        focus_context = ", ".join(focus_areas)
        
        prompt = f"""Please summarize the following content with special attention to these focus areas: {focus_context}.

CONTENT TO SUMMARIZE:
{content}

USER TONE PROFILE:
{tone_context}

FOCUS AREAS:
{focus_context}

REQUIREMENTS:
- Maximum summary length: {max_length} words
- Prioritize insights related to the specified focus areas
- Extract key points that address these areas of interest
- Match the user's communication style
- Ensure professional relevance for LinkedIn audience
- Balance focus areas while maintaining content coherence

Please provide a focused summary that emphasizes the specified areas while maintaining overall content value."""
        
        return prompt
    
    def _build_tone_context(self, tone_profile: ToneProfile) -> str:
        """Build tone context from user profile."""
        context_parts = []
        
        # Writing style
        context_parts.append(f"Writing Style: {tone_profile.writing_style.value}")
        
        # Communication tone
        context_parts.append(f"Communication Tone: {tone_profile.tone.value}")
        
        # Personality traits
        if tone_profile.personality_traits:
            traits = ", ".join(tone_profile.personality_traits)
            context_parts.append(f"Personality Traits: {traits}")
        
        # Industry focus
        if tone_profile.industry_focus:
            industries = ", ".join(tone_profile.industry_focus)
            context_parts.append(f"Industry Focus: {industries}")
        
        # Communication preferences
        prefs = tone_profile.communication_preferences
        pref_details = []
        
        if prefs.get("use_emojis"):
            pref_details.append("uses emojis appropriately")
        
        if prefs.get("call_to_action_style") == "direct":
            pref_details.append("prefers direct engagement")
        elif prefs.get("call_to_action_style") == "subtle":
            pref_details.append("prefers subtle engagement")
        
        preferred_length = prefs.get("preferred_length", "medium")
        pref_details.append(f"prefers {preferred_length} length content")
        
        if pref_details:
            context_parts.append(f"Communication Preferences: {', '.join(pref_details)}")
        
        return "\n".join(context_parts)
    
    def _get_industry_context(self, industry: str) -> str:
        """Get industry-specific context for summarization."""
        industry_contexts = {
            "technology": "Focus on innovation, digital transformation, technical insights, and emerging technologies. Use technical terminology appropriately.",
            "finance": "Emphasize market trends, financial insights, investment perspectives, and economic implications. Include relevant financial metrics.",
            "healthcare": "Highlight patient outcomes, medical innovations, healthcare policy, and industry developments. Use appropriate medical terminology.",
            "education": "Focus on learning outcomes, educational innovation, teaching methodologies, and academic insights. Emphasize knowledge transfer.",
            "marketing": "Emphasize brand insights, customer engagement, marketing strategies, and campaign effectiveness. Include relevant metrics and trends.",
            "sales": "Focus on sales strategies, customer relationships, revenue insights, and market opportunities. Highlight actionable sales tactics.",
            "consulting": "Emphasize strategic insights, problem-solving approaches, best practices, and transformation initiatives. Focus on actionable advice.",
            "entrepreneurship": "Highlight innovation, business development, startup insights, and growth strategies. Focus on practical business advice."
        }
        
        return industry_contexts.get(industry.lower(), 
            "Focus on professional insights, industry trends, and actionable advice relevant to business professionals.")
    
    def build_executive_summary_prompt(
        self,
        content: str,
        tone_profile: ToneProfile,
        max_length: int = 150
    ) -> str:
        """
        Build prompt for executive-style summary.
        
        Args:
            content: Content to summarize
            tone_profile: User's tone profile
            max_length: Maximum summary length
            
        Returns:
            Executive summary prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        
        prompt = f"""Please create an executive-style summary of the following content for senior professionals on LinkedIn.

CONTENT TO SUMMARIZE:
{content}

USER TONE PROFILE:
{tone_context}

EXECUTIVE SUMMARY REQUIREMENTS:
- Maximum length: {max_length} words
- Lead with the most critical insight or conclusion
- Focus on strategic implications and business impact
- Use executive-level language and terminology
- Highlight key decisions, trends, or opportunities
- Structure for quick scanning by busy executives
- Include quantifiable results or metrics when available

Please provide a concise executive summary that delivers maximum value in minimum time."""
        
        return prompt
    
    def build_technical_summary_prompt(
        self,
        content: str,
        tone_profile: ToneProfile,
        technical_level: str = "intermediate",
        max_length: int = 200
    ) -> str:
        """
        Build prompt for technical content summary.
        
        Args:
            content: Content to summarize
            tone_profile: User's tone profile
            technical_level: Level of technical detail (basic, intermediate, advanced)
            max_length: Maximum summary length
            
        Returns:
            Technical summary prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        
        technical_guidance = {
            "basic": "Use accessible language, explain technical terms, focus on practical applications",
            "intermediate": "Use standard technical terminology, balance detail with accessibility",
            "advanced": "Use precise technical language, include implementation details and technical nuances"
        }
        
        guidance = technical_guidance.get(technical_level, technical_guidance["intermediate"])
        
        prompt = f"""Please create a technical summary of the following content for LinkedIn professionals.

CONTENT TO SUMMARIZE:
{content}

USER TONE PROFILE:
{tone_context}

TECHNICAL SUMMARY REQUIREMENTS:
- Maximum length: {max_length} words
- Technical level: {technical_level} - {guidance}
- Focus on technical insights, methodologies, and implementations
- Include relevant technical details and specifications
- Highlight practical applications and use cases
- Structure for technical professionals and decision makers

Please provide a technical summary that balances detail with professional accessibility."""
        
        return prompt
    
    def build_trend_analysis_prompt(
        self,
        content: str,
        tone_profile: ToneProfile,
        max_length: int = 200
    ) -> str:
        """
        Build prompt for trend analysis summary.
        
        Args:
            content: Content to summarize
            tone_profile: User's tone profile
            max_length: Maximum summary length
            
        Returns:
            Trend analysis summary prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        
        prompt = f"""Please create a trend analysis summary of the following content for LinkedIn professionals.

CONTENT TO SUMMARIZE:
{content}

USER TONE PROFILE:
{tone_context}

TREND ANALYSIS REQUIREMENTS:
- Maximum length: {max_length} words
- Identify key trends, patterns, and emerging developments
- Highlight implications for professionals and businesses
- Include forward-looking insights and predictions
- Focus on actionable intelligence for decision makers
- Connect trends to broader industry or market context
- Emphasize opportunities and potential challenges

Please provide a trend-focused summary that helps professionals understand market direction and implications."""
        
        return prompt