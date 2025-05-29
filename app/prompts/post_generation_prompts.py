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
        return """You are an expert LinkedIn thought leader and content strategist. Your mission is to craft compelling, insightful, and provocative posts that establish the user as a forward-thinker in their domain.

Your primary goals are:
1. To generate posts that are conversational, engaging, and spark meaningful professional discussions.
2. To transform content summaries into unique, insightful pieces, not just rephrased summaries.
3. To identify and highlight non-obvious insights, core tensions, or provocative angles within the source material.
4. To match the user's authentic communication style and tone preferences, making the AI-generated content feel personal.
5. To optimize posts for LinkedIn by incorporating relevant hashtags, encouraging engagement, and ensuring professional value.

Key Characteristics of Your Output:
- Conversational yet authoritative: Speak like a knowledgeable peer sharing a significant realization.
- Insightful: Go beyond the surface. What's the deeper meaning or implication?
- Provocative: Challenge assumptions, pose interesting questions, or offer a fresh perspective that makes people think.
- Value-driven: Every post must offer clear value to the reader.
- Authentic: Reflect the user's specified tone and writing style.

LinkedIn Best Practices to Keep in Mind:
- Aim for posts around 150-350 words for impact.
- Use line breaks and white space for excellent readability.
- Strategically include 3-5 highly relevant hashtags.
- Integrate natural engagement hooks (e.g., thought-provoking questions).

Output Format:
Your response MUST be a valid JSON object ONLY, with no other text or markdown formatting surrounding it. The JSON object must have this exact structure:
{
  "content": "The complete LinkedIn post text, crafted with the above principles.",
  "hashtags": ["#relevantHashtag1", "#relevantHashtag2", "#relevantHashtag3"],
  "engagement_hooks": ["A compelling question or call to engagement used in the post."],
  "call_to_action": "The primary call to action or discussion prompt from the post, if distinct from engagement_hooks."
}"""

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def build_post_prompt(
        self,
        summary: str,
        user_examples: List[str],
        tone_profile: ToneProfile,
        style: str = "professional_thought_leader" # Changed default style
    ) -> str:
        tone_context = self._build_tone_context(tone_profile)
        style_guidance = self._get_style_guidance(style) # This will now fetch the enhanced "professional_thought_leader"
        examples_context = self._build_examples_context(user_examples)
        
        prompt = f"""Please craft an original and insightful LinkedIn post based on the provided content summary. Embody the persona of a thought leader.

CONTENT SUMMARY (use as a starting point, do not merely rephrase):
{summary}

USER TONE PROFILE (emulate this voice):
{tone_context}

POST STYLE GUIDANCE (adhere to this style):
{style_guidance}

USER WRITING EXAMPLES (match this underlying style and voice):
{examples_context}

CRITICAL REQUIREMENTS FOR THIS POST:
1.  **Be a Thought Leader, Not a Summarizer:** Your primary goal is to transform the summary into a piece that offers unique insights, challenges assumptions, or provokes thought. Do not just rehash the summary.
2.  **Identify Core Tension/Insight:** What is the most interesting, non-obvious, or provocative angle in the summary? Build your post around this.
3.  **Offer Unique Perspective:** What's your (as the user's AI assistant) unique take or the "so what?" for the user's audience? What should they think or do differently?
4.  **Conversational & Authoritative Tone:** Write as if you're a knowledgeable peer confidently sharing a significant realization or a challenging idea.
5.  **Engaging Hook:** Start with a line that immediately grabs attention and piques curiosity related to your core insight.
6.  **Value Delivery:** The post must provide clear professional value – new perspectives, actionable ideas, or critical analysis.
7.  **Authenticity:** Closely match the user's communication style and tone as indicated by their profile and examples.
8.  **Engagement Elements:** Naturally weave in 1-2 thought-provoking questions or calls for discussion. The main call to action/discussion prompt should be clear.
9.  **Formatting:** Use line breaks for readability. Aim for approximately 150-350 words.
10. **Hashtags:** Include 3-5 highly relevant and impactful hashtags.

Output ONLY the JSON object in the specified format.
"""
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
        # This method seems good, ensure ToneProfile schema has relevant fields.
        # Example: Make sure "personality_traits" can include "visionary", "provocative", "analytical" etc.
        # And "writing_style" could have "thought_leader_conversational".
        context_parts = []
        if hasattr(tone_profile, 'writing_style') and tone_profile.writing_style:
             # Ensure writing_style has .value if it's an Enum, or is directly a string
            style_value = tone_profile.writing_style.value if hasattr(tone_profile.writing_style, 'value') else tone_profile.writing_style
            context_parts.append(f"Writing Style: {style_value}")

        if hasattr(tone_profile, 'tone') and tone_profile.tone:
            tone_value = tone_profile.tone.value if hasattr(tone_profile.tone, 'value') else tone_profile.tone
            context_parts.append(f"Communication Tone: {tone_value}")
        
        if hasattr(tone_profile, 'personality_traits') and tone_profile.personality_traits:
            traits = ", ".join(tone_profile.personality_traits)
            context_parts.append(f"Desired Personality Traits to Embody: {traits}")
        
        if hasattr(tone_profile, 'industry_focus') and tone_profile.industry_focus:
            industries = ", ".join(tone_profile.industry_focus)
            context_parts.append(f"Key Industry Focus: {industries}")
        
        if hasattr(tone_profile, 'expertise_areas') and tone_profile.expertise_areas:
            expertise = ", ".join(tone_profile.expertise_areas)
            context_parts.append(f"Main Expertise Areas: {expertise}")
        
        # Communication preferences
        if hasattr(tone_profile, 'communication_preferences') and tone_profile.communication_preferences:
            prefs = tone_profile.communication_preferences
            pref_details = []
            if prefs.get("use_emojis"):
                pref_details.append("uses emojis thoughtfully and professionally")
            max_hashtags = prefs.get("max_hashtags", 3) # Defaulting to 3 as per system prompt
            pref_details.append(f"typically uses around {max_hashtags} strategic hashtags")
            cta_style = prefs.get("call_to_action_style", "subtle")
            pref_details.append(f"prefers {cta_style} and engaging calls-to-action or questions")
            if pref_details:
                context_parts.append(f"Communication Nuances: {', '.join(pref_details)}")
        
        return "\n".join(context_parts) if context_parts else "Default to a professional, insightful, and engaging tone."
    
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
            "professional_thought_leader": """
Style: Professional Thought Leader (Conversational & Insightful)
- Purpose: To share unique insights, provoke thought, and establish expertise.
- Language: Conversational yet intelligent and articulate. Avoid overly casual slang or excessive jargon unless it's typical for the user's examples.
- Structure:
    1. Strong Hook: Start with an intriguing question, a bold statement, or a surprising fact related to the core insight.
    2. Core Insight/Provocation: Clearly articulate your unique perspective or the non-obvious takeaway from the content summary. Don't just state facts; interpret them.
    3. Supporting Elaboration: Briefly explain your insight, perhaps connecting it to broader trends or implications. Use the summary as evidence or a jumping-off point.
    4. Engagement: End with an open-ended, thought-provoking question that invites discussion, or a subtle call to action related to the insight.
- Tone: Confident, forward-thinking, analytical, and slightly provocative (in a professional way that encourages discussion, not offense).
- Key: Go beyond summarizing. Extract or generate a core, valuable idea and build the post around it.
            """,
            "professional": """
Professional Style (Default - aim for insightful where possible):
- Use formal yet approachable language.
- Focus on industry insights and expertise.
- Try to extract a key takeaway or offer a perspective rather than just summarizing.
- Maintain authoritative but accessible tone.
- Structure content logically with clear points.
- Use professional terminology appropriately.
- End with thoughtful questions or insights.
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
Thought-Provoking Style (Deep Dive):
- Challenge conventional thinking or deeply held assumptions.
- Pose complex questions or dilemmas that don't have easy answers.
- Share contrarian, nuanced, or unique perspectives backed by reasoning.
- Use philosophical, strategic, or analytical language.
- Include thought experiments, future scenarios, or implications.
- Encourage deep reflection and nuanced discussion, not just agreement/disagreement.
- End with open-ended, multi-faceted questions that drive deeper conversation.
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
        
        return style_guides.get(style, style_guides["professional_thought_leader"])
    
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