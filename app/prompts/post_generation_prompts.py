"""
Post generation prompts for LinkedIn Presence Automation Application.

Contains prompt templates and builders for LinkedIn post generation with
style variations, engagement optimization, and tone matching.
"""

from typing import Dict, Any, Optional, List
from app.schemas.ai_schemas import ToneProfile, PostStyleEnum


class PostGenerationPrompts:
    """
    Prompt templates and builders for LinkedIn post generation.
    
    Provides structured prompts for creating engaging LinkedIn posts with
    various styles, tone matching, and engagement optimization.
    """
    
    def __init__(self):
        """Initialize post generation prompts."""
        self.system_prompt = self._build_system_prompt()
        self.style_templates = self._build_style_templates()
        self.engagement_hooks = self._build_engagement_hooks()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for post generation."""
        return """You are an expert LinkedIn content creator specializing in professional post generation.

Your role is to:
1. Create engaging LinkedIn posts that drive professional engagement
2. Match the user's communication style and tone preferences
3. Optimize content for LinkedIn's algorithm and audience
4. Include relevant hashtags and engagement elements
5. Ensure content provides professional value

LinkedIn Best Practices:
- Posts should be 150-300 words for optimal engagement
- Use line breaks and white space for readability
- Include 3-5 relevant hashtags
- Add engagement hooks (questions, calls-to-action)
- Focus on professional insights, experiences, or advice
- Use storytelling when appropriate
- Maintain authenticity and personal voice

Content Guidelines:
- Start with a compelling hook in the first line
- Provide value through insights, tips, or experiences
- Use conversational yet professional tone
- Include specific examples or data when possible
- End with engagement-driving questions or calls-to-action
- Ensure content is scannable with proper formatting

Output Format:
Provide your response as a JSON object with:
{
  "content": "The complete LinkedIn post text",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
  "engagement_hooks": ["Hook 1", "Hook 2"],
  "call_to_action": "Specific call to action used"
}"""
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for post generation."""
        return self.system_prompt
    
    def build_post_prompt(
        self,
        summary: str,
        user_examples: List[str],
        tone_profile: ToneProfile,
        style: str = "professional"
    ) -> str:
        """
        Build LinkedIn post generation prompt.
        
        Args:
            summary: Content summary to generate post from
            user_examples: User's historical posts for style matching
            tone_profile: User's tone profile
            style: Desired post style
            
        Returns:
            Formatted post generation prompt
        """
        # Build context sections
        tone_context = self._build_tone_context(tone_profile)
        style_guidance = self._get_style_guidance(style)
        examples_context = self._build_examples_context(user_examples)
        
        prompt = f"""Please create a LinkedIn post based on the following content summary.

CONTENT SUMMARY:
{summary}

USER TONE PROFILE:
{tone_context}

POST STYLE GUIDANCE:
{style_guidance}

USER WRITING EXAMPLES:
{examples_context}

REQUIREMENTS:
- Create an engaging LinkedIn post (150-300 words)
- Match the user's communication style shown in examples
- Follow the specified post style guidance
- Include 3-5 relevant hashtags
- Add engagement elements (questions, calls-to-action)
- Use proper formatting with line breaks for readability
- Ensure professional value and authenticity
- Start with a compelling hook
- End with engagement-driving element

Please generate a LinkedIn post that captures the essence of the content while matching the user's authentic voice and style."""
        
        return prompt
    
    def build_storytelling_post_prompt(
        self,
        summary: str,
        tone_profile: ToneProfile,
        user_examples: List[str],
        story_angle: str = "lesson_learned"
    ) -> str:
        """
        Build storytelling-focused post prompt.
        
        Args:
            summary: Content summary
            tone_profile: User's tone profile
            user_examples: User's historical posts
            story_angle: Type of story angle to use
            
        Returns:
            Storytelling post prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        examples_context = self._build_examples_context(user_examples)
        story_guidance = self._get_story_guidance(story_angle)
        
        prompt = f"""Please create a storytelling LinkedIn post based on the following content.

CONTENT SUMMARY:
{summary}

USER TONE PROFILE:
{tone_context}

USER WRITING EXAMPLES:
{examples_context}

STORYTELLING APPROACH:
{story_guidance}

STORYTELLING REQUIREMENTS:
- Structure as a compelling narrative (200-350 words)
- Start with an engaging hook or scene-setting
- Include a clear challenge, insight, or transformation
- Connect the story to broader professional lessons
- Use specific details to make the story relatable
- End with actionable takeaways or questions
- Maintain authenticity and personal voice
- Include relevant hashtags and engagement elements

Please create a story-driven LinkedIn post that engages readers while delivering professional value."""
        
        return prompt
    
    def build_thought_leadership_prompt(
        self,
        summary: str,
        tone_profile: ToneProfile,
        user_examples: List[str],
        industry_focus: Optional[str] = None
    ) -> str:
        """
        Build thought leadership post prompt.
        
        Args:
            summary: Content summary
            tone_profile: User's tone profile
            user_examples: User's historical posts
            industry_focus: Specific industry to focus on
            
        Returns:
            Thought leadership post prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        examples_context = self._build_examples_context(user_examples)
        industry_context = self._get_industry_context(industry_focus) if industry_focus else ""
        
        prompt = f"""Please create a thought leadership LinkedIn post based on the following content.

CONTENT SUMMARY:
{summary}

USER TONE PROFILE:
{tone_context}

USER WRITING EXAMPLES:
{examples_context}

{industry_context}

THOUGHT LEADERSHIP REQUIREMENTS:
- Position the user as an industry expert or thought leader
- Share unique insights, perspectives, or predictions
- Include data, trends, or evidence to support points
- Offer actionable advice or strategic thinking
- Use authoritative yet accessible language
- Structure for maximum professional impact
- Include forward-looking statements or predictions
- End with discussion-provoking questions
- Optimize for professional sharing and commenting

Please create a thought leadership post that establishes expertise while driving meaningful professional discussion."""
        
        return prompt
    
    def build_educational_post_prompt(
        self,
        summary: str,
        tone_profile: ToneProfile,
        user_examples: List[str],
        learning_format: str = "tips"
    ) -> str:
        """
        Build educational post prompt.
        
        Args:
            summary: Content summary
            tone_profile: User's tone profile
            user_examples: User's historical posts
            learning_format: Format for educational content (tips, steps, framework)
            
        Returns:
            Educational post prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        examples_context = self._build_examples_context(user_examples)
        format_guidance = self._get_educational_format_guidance(learning_format)
        
        prompt = f"""Please create an educational LinkedIn post based on the following content.

CONTENT SUMMARY:
{summary}

USER TONE PROFILE:
{tone_context}

USER WRITING EXAMPLES:
{examples_context}

EDUCATIONAL FORMAT:
{format_guidance}

EDUCATIONAL POST REQUIREMENTS:
- Structure content for easy learning and application
- Use clear, actionable language
- Include specific examples or case studies
- Break down complex concepts into digestible parts
- Provide practical takeaways readers can implement
- Use formatting (numbers, bullets) for clarity
- Include relevant hashtags for discoverability
- End with engagement questions about implementation

Please create an educational post that teaches valuable skills or knowledge while maintaining engagement."""
        
        return prompt
    
    def build_engagement_optimized_prompt(
        self,
        summary: str,
        tone_profile: ToneProfile,
        user_examples: List[str],
        engagement_goal: str = "comments"
    ) -> str:
        """
        Build engagement-optimized post prompt.
        
        Args:
            summary: Content summary
            tone_profile: User's tone profile
            user_examples: User's historical posts
            engagement_goal: Primary engagement goal (comments, shares, likes)
            
        Returns:
            Engagement-optimized post prompt
        """
        tone_context = self._build_tone_context(tone_profile)
        examples_context = self._build_examples_context(user_examples)
        engagement_strategy = self._get_engagement_strategy(engagement_goal)
        
        prompt = f"""Please create a highly engaging LinkedIn post optimized for {engagement_goal}.

CONTENT SUMMARY:
{summary}

USER TONE PROFILE:
{tone_context}

USER WRITING EXAMPLES:
{examples_context}

ENGAGEMENT STRATEGY:
{engagement_strategy}

ENGAGEMENT OPTIMIZATION REQUIREMENTS:
- Optimize specifically for {engagement_goal}
- Use proven engagement techniques and hooks
- Include multiple engagement triggers throughout
- Create content that encourages professional discussion
- Use formatting that enhances readability and engagement
- Include strategic hashtags for maximum reach
- End with compelling calls-to-action
- Balance value delivery with engagement optimization

Please create a post that maximizes {engagement_goal} while maintaining professional value and authenticity."""
        
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
        
        max_hashtags = prefs.get("max_hashtags", 3)
        pref_details.append(f"uses {max_hashtags} hashtags typically")
        
        cta_style = prefs.get("call_to_action_style", "subtle")
        pref_details.append(f"prefers {cta_style} calls-to-action")
        
        if pref_details:
            context_parts.append(f"Communication Preferences: {', '.join(pref_details)}")
        
        return "\n".join(context_parts)
    
    def _build_examples_context(self, user_examples: List[str]) -> str:
        """Build context from user's historical posts."""
        if not user_examples:
            return "No previous examples available - use professional LinkedIn best practices."
        
        # Limit examples and provide context
        limited_examples = user_examples[:3]  # Use up to 3 examples
        
        context = "Previous posts by this user (match this style and voice):\n\n"
        for i, example in enumerate(limited_examples, 1):
            # Truncate long examples
            truncated_example = example[:300] + "..." if len(example) > 300 else example
            context += f"Example {i}:\n{truncated_example}\n\n"
        
        context += "Please match the writing style, tone, and voice demonstrated in these examples."
        
        return context
    
    def _get_style_guidance(self, style: str) -> str:
        """Get style-specific guidance."""
        style_guides = {
            "professional": """
Professional Style Guidelines:
- Use formal yet approachable language
- Focus on industry insights and expertise
- Include data, metrics, or evidence when relevant
- Maintain authoritative but accessible tone
- Structure content logically with clear points
- Use professional terminology appropriately
- End with thoughtful questions or insights
            """,
            "casual": """
Casual Style Guidelines:
- Use conversational, friendly language
- Share personal experiences and stories
- Include relatable examples and analogies
- Use contractions and informal expressions
- Add personality and humor when appropriate
- Focus on human connections and relatability
- End with engaging, personal questions
            """,
            "thought_provoking": """
Thought-Provoking Style Guidelines:
- Challenge conventional thinking or assumptions
- Pose interesting questions or dilemmas
- Share contrarian or unique perspectives
- Use philosophical or strategic language
- Include thought experiments or scenarios
- Encourage deep reflection and discussion
- End with open-ended, discussion-driving questions
            """,
            "educational": """
Educational Style Guidelines:
- Structure content as learning material
- Use clear, instructional language
- Include step-by-step guidance or frameworks
- Provide actionable takeaways and tips
- Use examples and case studies
- Focus on skill development and knowledge transfer
- End with implementation questions or challenges
            """,
            "motivational": """
Motivational Style Guidelines:
- Use inspiring and uplifting language
- Share success stories and achievements
- Include motivational quotes or principles
- Focus on growth, potential, and possibilities
- Use energetic and positive tone
- Encourage action and personal development
- End with empowering calls-to-action
            """
        }
        
        return style_guides.get(style, style_guides["professional"])
    
    def _get_story_guidance(self, story_angle: str) -> str:
        """Get storytelling guidance based on angle."""
        story_guides = {
            "lesson_learned": """
Lesson Learned Story Structure:
- Start with a challenging situation or mistake
- Describe the journey and realization process
- Share the key insight or lesson discovered
- Connect to broader professional applications
- End with actionable advice for others
            """,
            "success_story": """
Success Story Structure:
- Begin with the goal or challenge faced
- Describe the strategy and execution process
- Highlight key moments and decisions
- Share the successful outcome and metrics
- Extract transferable lessons for others
            """,
            "transformation": """
Transformation Story Structure:
- Describe the initial state or problem
- Share the catalyst for change
- Detail the transformation process
- Highlight the new state and benefits
- Provide guidance for others seeking similar change
            """,
            "behind_the_scenes": """
Behind-the-Scenes Story Structure:
- Reveal the unseen aspects of a process
- Share insider insights and perspectives
- Include specific details and examples
- Explain the 'why' behind decisions
- Provide valuable context for others
            """
        }
        
        return story_guides.get(story_angle, story_guides["lesson_learned"])
    
    def _get_industry_context(self, industry: str) -> str:
        """Get industry-specific context."""
        return f"""
INDUSTRY FOCUS: {industry.title()}
- Use industry-relevant terminology and examples
- Reference current trends and challenges in {industry}
- Connect insights to {industry} professional concerns
- Include metrics or data relevant to {industry}
- Address pain points specific to {industry} professionals
        """
    
    def _get_educational_format_guidance(self, format_type: str) -> str:
        """Get educational format guidance."""
        format_guides = {
            "tips": """
Tips Format:
- Structure as numbered or bulleted tips
- Make each tip actionable and specific
- Include brief explanations or examples
- Use parallel structure for consistency
- Limit to 3-7 tips for optimal engagement
            """,
            "steps": """
Step-by-Step Format:
- Present as a sequential process
- Number each step clearly
- Include what to do and why
- Provide specific actions for each step
- Include expected outcomes or results
            """,
            "framework": """
Framework Format:
- Present as a structured methodology
- Include clear components or phases
- Explain how parts work together
- Provide implementation guidance
- Include examples of framework application
            """,
            "checklist": """
Checklist Format:
- Structure as actionable checklist items
- Use clear, specific language
- Include verification criteria
- Organize logically by priority or sequence
- Make items easy to implement and verify
            """
        }
        
        return format_guides.get(format_type, format_guides["tips"])
    
    def _get_engagement_strategy(self, engagement_goal: str) -> str:
        """Get engagement strategy based on goal."""
        strategies = {
            "comments": """
Comment-Driving Strategy:
- Ask specific, thought-provoking questions
- Share controversial or debatable points (professionally)
- Request personal experiences or opinions
- Use "What's your take?" or "Agree or disagree?"
- Include multiple discussion points
- End with open-ended questions
            """,
            "shares": """
Share-Optimized Strategy:
- Create highly valuable, actionable content
- Include surprising insights or data
- Use compelling statistics or research
- Create "save for later" worthy content
- Include quotable statements or key takeaways
- Focus on evergreen, reference-worthy information
            """,
            "likes": """
Like-Optimized Strategy:
- Use relatable, agreeable statements
- Include inspirational or motivational content
- Share widely accepted professional truths
- Use positive, uplifting language
- Include recognition or appreciation posts
- Create content that validates reader experiences
            """
        }
        
        return strategies.get(engagement_goal, strategies["comments"])
    
    def _build_style_templates(self) -> Dict[str, str]:
        """Build style-specific templates."""
        return {
            "professional": "Share expertise → Provide insights → Ask thoughtful questions",
            "casual": "Personal story → Relatable lesson → Friendly engagement",
            "thought_provoking": "Challenge assumption → Present perspective → Provoke discussion",
            "educational": "Teach concept → Provide examples → Encourage application",
            "motivational": "Inspire action → Share success → Empower others"
        }
    
    def _build_engagement_hooks(self) -> Dict[str, List[str]]:
        """Build engagement hook templates."""
        return {
            "question_starters": [
                "What's your experience with...",
                "How do you handle...",
                "What would you add to...",
                "Agree or disagree:",
                "What's your take on..."
            ],
            "story_hooks": [
                "Here's what I learned when...",
                "Last week, something happened that...",
                "I used to think... until...",
                "The biggest mistake I see...",
                "Here's a story that changed my perspective..."
            ],
            "insight_hooks": [
                "After analyzing 100+ cases...",
                "The data shows something surprising...",
                "Most people believe... but the reality is...",
                "Here's what successful people do differently...",
                "The secret that nobody talks about..."
            ]
        }