"""
Comment generation prompts for LinkedIn Presence Automation Application.

Contains prompt templates and builders for LinkedIn comment generation with
engagement optimization and tone matching.
"""

from typing import Dict, Any, Optional, List
from app.schemas.ai_schemas import ToneProfile


class CommentPrompts:
    """
    Prompt templates and builders for LinkedIn comment generation.

    Provides structured prompts for creating engaging LinkedIn comments with
    various engagement types, tone matching, and professional appropriateness.
    """

    def __init__(self):
        """Initialize comment generation prompts."""
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt for comment generation."""
        return """You are an expert LinkedIn engagement specialist focused on creating meaningful, professional comments.

Your role is to:
1. Generate thoughtful comments that add value to LinkedIn conversations
2. Match the user's communication style and tone preferences
3. Create comments that encourage further discussion and engagement
4. Maintain professional appropriateness for LinkedIn's business context
5. Avoid generic or spam-like responses

LinkedIn Comment Best Practices:
- Comments should be 50-150 characters for optimal engagement
- Add genuine value or insight to the conversation
- Ask thoughtful follow-up questions when appropriate
- Share relevant personal experiences or perspectives
- Acknowledge the original poster's insights
- Use professional language while maintaining authenticity
- Avoid overly promotional content

Comment Types:
- Thoughtful: Provide insights or perspectives on the topic
- Supportive: Show agreement and encouragement
- Questioning: Ask clarifying or thought-provoking questions
- Congratulatory: Celebrate achievements or milestones
- Insightful: Share additional knowledge or experience

Output Format:
Provide your response as a JSON object with:
{
  "comment": "The generated comment text",
  "engagement_type": "Type of engagement used",
  "confidence_score": 0.8,
  "alternative_comments": ["Alternative 1", "Alternative 2"]
}"""

    def get_system_prompt(self) -> str:
        """Get the system prompt for comment generation."""
        return self.system_prompt

    def build_comment_prompt(
        self,
        post_content: str,
        tone_profile: ToneProfile,
        post_author: Optional[str] = None,
        engagement_type: str = "thoughtful",
        max_length: int = 150,
        context: Optional[str] = None
    ) -> str:
        """
        Build LinkedIn comment generation prompt.

        Args:
            post_content: Content of the LinkedIn post to comment on
            tone_profile: User's tone profile for style matching
            post_author: Optional author of the post
            engagement_type: Type of engagement desired
            max_length: Maximum comment length
            context: Optional additional context

        Returns:
            Formatted comment generation prompt
        """
        # Build context sections
        tone_context = self._build_tone_context(tone_profile)
        engagement_guidance = self._get_engagement_guidance(engagement_type)
        author_context = f"Post Author: {post_author}" if post_author else "Post Author: Not specified"

        prompt = f"""Please generate a LinkedIn comment for the following post.

POST CONTENT:
{post_content}

{author_context}

USER TONE PROFILE:
{tone_context}

ENGAGEMENT TYPE: {engagement_type}
{engagement_guidance}

REQUIREMENTS:
- Maximum comment length: {max_length} characters
- Match the user's communication style and tone
- Create a {engagement_type} response that adds value
- Maintain professional appropriateness for LinkedIn
- Avoid generic responses like "Great post!" or "Thanks for sharing!"
- Be specific and relevant to the post content
- Encourage further discussion when appropriate

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

Please generate a comment that demonstrates genuine engagement while maintaining the user's authentic professional voice."""

        return prompt

    def build_reply_comment_prompt(
        self,
        original_post: str,
        parent_comment: str,
        tone_profile: ToneProfile,
        engagement_type: str = "thoughtful"
    ) -> str:
        """
        Build prompt for replying to an existing comment.

        Args:
            original_post: Original post content
            parent_comment: Comment being replied to
            tone_profile: User's tone profile
            engagement_type: Type of engagement desired

        Returns:
            Reply comment generation prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        engagement_guidance = self._get_engagement_guidance(engagement_type)

        prompt = f"""Please generate a reply to a LinkedIn comment thread.

ORIGINAL POST:
{original_post}

COMMENT BEING REPLIED TO:
{parent_comment}

USER TONE PROFILE:
{tone_context}

ENGAGEMENT TYPE: {engagement_type}
{engagement_guidance}

REPLY REQUIREMENTS:
- Respond directly to the parent comment
- Maintain context of the original post
- Add value to the conversation thread
- Keep reply concise (50-100 characters)
- Match the user's communication style
- Be respectful and professional
- Avoid repeating points already made

Please generate a thoughtful reply that continues the conversation meaningfully."""

        return prompt

    def build_congratulatory_comment_prompt(
        self,
        achievement_post: str,
        tone_profile: ToneProfile,
        relationship_context: Optional[str] = None
    ) -> str:
        """
        Build prompt for congratulatory comments on achievements.

        Args:
            achievement_post: Post about an achievement or milestone
            tone_profile: User's tone profile
            relationship_context: Optional context about relationship with poster

        Returns:
            Congratulatory comment prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        relationship_info = f"RELATIONSHIP CONTEXT: {relationship_context}" if relationship_context else ""

        prompt = f"""Please generate a congratulatory comment for a LinkedIn achievement post.

ACHIEVEMENT POST:
{achievement_post}

USER TONE PROFILE:
{tone_context}

{relationship_info}

CONGRATULATORY COMMENT REQUIREMENTS:
- Acknowledge the specific achievement mentioned
- Express genuine congratulations
- Keep the tone positive and professional
- Personalize based on the achievement type
- Avoid generic phrases like "Congrats!" alone
- Match the user's communication style
- Consider adding a brief personal note if relationship context provided

Please generate a heartfelt congratulatory comment that feels authentic and specific to the achievement."""

        return prompt

    def build_question_comment_prompt(
        self,
        post_content: str,
        tone_profile: ToneProfile,
        question_focus: Optional[str] = None
    ) -> str:
        """
        Build prompt for question-based comments.

        Args:
            post_content: Content of the post
            tone_profile: User's tone profile
            question_focus: Optional focus area for the question

        Returns:
            Question comment generation prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        focus_guidance = f"QUESTION FOCUS: {question_focus}" if question_focus else ""

        prompt = f"""Please generate a question-based comment for a LinkedIn post.

POST CONTENT:
{post_content}

USER TONE PROFILE:
{tone_context}

{focus_guidance}

QUESTION COMMENT REQUIREMENTS:
- Ask a thoughtful, relevant question about the post content
- Encourage the author to elaborate or share more insights
- Show genuine curiosity and interest
- Avoid questions that can be answered with simple yes/no
- Make the question specific to the post content
- Match the user's communication style
- Keep the question concise but engaging

Please generate a question that demonstrates genuine interest and encourages meaningful discussion."""

        return prompt

    def build_experience_sharing_prompt(
        self,
        post_content: str,
        tone_profile: ToneProfile,
        user_experience: Optional[str] = None
    ) -> str:
        """
        Build prompt for sharing relevant experience in comments.

        Args:
            post_content: Content of the post
            tone_profile: User's tone profile
            user_experience: Optional user experience to reference

        Returns:
            Experience sharing comment prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        experience_context = f"USER EXPERIENCE TO REFERENCE: {user_experience}" if user_experience else ""

        prompt = f"""Please generate a comment that shares relevant experience related to the post.

POST CONTENT:
{post_content}

USER TONE PROFILE:
{tone_context}

{experience_context}

EXPERIENCE SHARING REQUIREMENTS:
- Share a relevant personal or professional experience
- Connect the experience to the post content meaningfully
- Add value through the shared perspective
- Keep the focus on adding to the conversation, not self-promotion
- Be authentic and specific
- Match the user's communication style
- Conclude with a question or invitation for further discussion

Please generate a comment that shares experience in a way that enriches the conversation."""

        return prompt

    def _build_tone_context(self, tone_profile: ToneProfile) -> str:
        """Build tone context from user profile."""
        context_parts = []

        # Writing style and tone
        context_parts.append(f"Writing Style: {tone_profile.writing_style.value}")
        context_parts.append(f"Communication Tone: {tone_profile.tone.value}")

        # Personality traits
        if tone_profile.personality_traits:
            traits = ", ".join(tone_profile.personality_traits)
            context_parts.append(f"Personality Traits: {traits}")

        # Industry and expertise
        if tone_profile.industry_focus:
            industries = ", ".join(tone_profile.industry_focus)
            context_parts.append(f"Industry Focus: {industries}")

        if tone_profile.expertise_areas:
            expertise = ", ".join(tone_profile.expertise_areas)
            context_parts.append(f"Expertise Areas: {expertise}")

        # Communication preferences
        prefs = tone_profile.communication_preferences
        pref_details = []

        if prefs.get("use_emojis"):
            pref_details.append("uses emojis appropriately")

        cta_style = prefs.get("call_to_action_style", "subtle")
        pref_details.append(f"prefers {cta_style} engagement style")

        if pref_details:
            context_parts.append(f"Communication Preferences: {', '.join(pref_details)}")

        return "\n".join(context_parts)

    def _get_engagement_guidance(self, engagement_type: str) -> str:
        """Get engagement-specific guidance."""
        guidance_map = {
            "thoughtful": """
THOUGHTFUL ENGAGEMENT:
- Provide meaningful insights or perspectives
- Show you've carefully read and considered the post
- Add depth to the conversation
- Share relevant knowledge or experience
- Ask follow-up questions that encourage discussion
            """,
            "supportive": """
SUPPORTIVE ENGAGEMENT:
- Show agreement and encouragement
- Acknowledge the poster's insights or achievements
- Amplify positive messages
- Express appreciation for the content shared
- Offer encouragement or validation
            """,
            "questioning": """
QUESTIONING ENGAGEMENT:
- Ask clarifying questions about the content
- Seek additional information or perspectives
- Challenge ideas constructively
- Encourage deeper exploration of topics
- Show curiosity about specific aspects
            """,
            "congratulatory": """
CONGRATULATORY ENGAGEMENT:
- Celebrate achievements or milestones
- Express genuine happiness for the poster
- Acknowledge specific accomplishments
- Share in the excitement of good news
- Offer well-wishes for future success
            """,
            "insightful": """
INSIGHTFUL ENGAGEMENT:
- Share additional knowledge or expertise
- Provide different perspectives on the topic
- Add valuable information to the discussion
- Connect ideas to broader concepts
- Offer practical advice or suggestions
            """
        }

        return guidance_map.get(engagement_type, guidance_map["thoughtful"])

    def get_comment_templates(self) -> Dict[str, str]:
        """Get comment template examples for different engagement types."""
        return {
            "thoughtful": "This resonates with my experience in [field]. I've found that [insight]. What's been your approach to [specific aspect]?",
            "supportive": "Excellent points about [topic]! Your perspective on [specific point] particularly stands out. Thanks for sharing these insights.",
            "questioning": "Great post! I'm curious about [specific aspect]. How do you typically handle [related challenge]?",
            "congratulatory": "Congratulations on [specific achievement]! Your work in [area] has been impressive. Wishing you continued success!",
            "insightful": "Building on your point about [topic], I've seen similar results when [additional insight]. Have you considered [suggestion]?"
        }

    def validate_comment_appropriateness(self, comment: str) -> Dict[str, Any]:
        """
        Validate comment for LinkedIn appropriateness.

        Args:
            comment: Comment text to validate

        Returns:
            Validation results with suggestions
        """
        issues = []
        suggestions = []

        # Check length
        if len(comment) < 10:
            issues.append("Comment too short")
            suggestions.append("Add more substance to provide value")
        elif len(comment) > 300:
            issues.append("Comment too long")
            suggestions.append("Consider breaking into shorter, more digestible points")

        # Check for generic responses
        generic_phrases = [
            "great post", "thanks for sharing", "nice", "good point",
            "i agree", "well said", "awesome", "cool"
        ]

        comment_lower = comment.lower()
        if any(phrase in comment_lower for phrase in generic_phrases):
            if len(comment) < 50:  # Only flag if comment is short
                issues.append("Comment appears generic")
                suggestions.append("Add specific insights or questions to make it more engaging")

        # Check for promotional content
        promotional_indicators = [
            "check out my", "visit my", "buy", "purchase", "sale",
            "discount", "offer", "deal", "free trial"
        ]

        if any(indicator in comment_lower for indicator in promotional_indicators):
            issues.append("Comment appears promotional")
            suggestions.append("Focus on adding value to the conversation rather than promotion")

        # Check for appropriate professional tone
        informal_indicators = [
            "lol", "omg", "wtf", "tbh", "imo", "fyi"
        ]

        if any(indicator in comment_lower for indicator in informal_indicators):
            issues.append("Comment may be too informal for LinkedIn")
            suggestions.append("Use more professional language appropriate for LinkedIn")

        return {
            "is_appropriate": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "character_count": len(comment),
            "word_count": len(comment.split())
        }