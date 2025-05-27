"""
Tone analyzer service for LinkedIn Presence Automation Application.

Analyzes user's historical LinkedIn posts to extract writing patterns,
tone preferences, and communication style for AI content generation.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from collections import Counter
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import AIService
from app.repositories.content_repository import PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import DraftStatus
from app.schemas.ai_schemas import ToneProfile

logger = logging.getLogger(__name__)


class ToneAnalysisError(Exception):
    """Base exception for tone analysis errors."""
    pass


class ToneAnalyzer:
    """
    Service for analyzing user's writing tone and communication patterns.
    
    Extracts writing style, personality traits, and preferences from
    historical posts to create personalized tone profiles for AI generation.
    """
    
    def __init__(self):
        """Initialize tone analyzer."""
        self.ai_service = AIService()
        
        # Common professional vocabulary indicators
        self.professional_indicators = {
            'high': ['strategic', 'innovative', 'optimize', 'leverage', 'synergy', 'paradigm', 'methodology'],
            'medium': ['professional', 'experience', 'development', 'business', 'industry', 'market'],
            'low': ['work', 'job', 'company', 'team', 'project', 'meeting']
        }
        
        # Personality trait indicators
        self.personality_indicators = {
            'analytical': ['data', 'analysis', 'metrics', 'research', 'study', 'findings', 'evidence'],
            'creative': ['creative', 'innovative', 'design', 'artistic', 'imagination', 'inspiration'],
            'leadership': ['lead', 'manage', 'direct', 'guide', 'mentor', 'inspire', 'vision'],
            'collaborative': ['team', 'together', 'collaborate', 'partnership', 'community', 'shared'],
            'technical': ['technology', 'software', 'system', 'algorithm', 'code', 'technical', 'digital'],
            'entrepreneurial': ['startup', 'entrepreneur', 'business', 'venture', 'opportunity', 'growth']
        }
        
        # Engagement patterns
        self.engagement_patterns = {
            'question_asker': [r'\?', r'what do you think', r'thoughts?', r'opinions?'],
            'storyteller': [r'story', r'experience', r'journey', r'learned', r'remember'],
            'educator': [r'tip:', r'advice', r'lesson', r'learn', r'teach', r'guide'],
            'motivator': [r'inspire', r'motivate', r'achieve', r'success', r'goal', r'dream']
        }
    
    async def analyze_user_tone(
        self,
        session: AsyncSession,
        user_id: str,
        min_posts: int = 5
    ) -> ToneProfile:
        """
        Analyze user's tone from historical posts.
        
        Args:
            session: Database session
            user_id: User ID to analyze
            min_posts: Minimum number of posts required for analysis
            
        Returns:
            ToneProfile with analyzed characteristics
            
        Raises:
            ToneAnalysisError: If analysis fails or insufficient data
        """
        try:
            logger.info(f"Analyzing tone for user {user_id}")
            
            # Get user's published posts
            post_repo = PostDraftRepository(session)
            user_repo = UserRepository(session)
            
            published_posts = await post_repo.get_drafts_by_status(
                user_id=user_id,
                status=DraftStatus.PUBLISHED,
                limit=50
            )
            
            if len(published_posts) < min_posts:
                logger.warning(f"Insufficient posts for analysis: {len(published_posts)} < {min_posts}")
                return await self._get_default_tone_profile(session, user_id)
            
            # Extract text content
            post_texts = [post.content for post in published_posts if post.content]
            
            if not post_texts:
                return await self._get_default_tone_profile(session, user_id)
            
            # Perform comprehensive analysis
            analysis_results = {
                'writing_style': self._analyze_writing_style(post_texts),
                'tone': self._analyze_tone(post_texts),
                'personality_traits': self._analyze_personality_traits(post_texts),
                'communication_preferences': self._analyze_communication_preferences(post_texts),
                'engagement_patterns': self._analyze_engagement_patterns(post_texts),
                'vocabulary_level': self._analyze_vocabulary_level(post_texts),
                'post_structure': self._analyze_post_structure(post_texts)
            }
            
            # Create tone profile
            tone_profile = ToneProfile(
                writing_style=analysis_results['writing_style'],
                tone=analysis_results['tone'],
                personality_traits=analysis_results['personality_traits'],
                industry_focus=await self._extract_industry_focus(post_texts),
                expertise_areas=await self._extract_expertise_areas(post_texts),
                communication_preferences=analysis_results['communication_preferences']
            )
            
            # Update user's tone profile in database
            await self._save_tone_profile(session, user_id, tone_profile, analysis_results)
            
            logger.info(f"Tone analysis completed for user {user_id}")
            return tone_profile
            
        except Exception as e:
            logger.error(f"Tone analysis failed for user {user_id}: {str(e)}")
            raise ToneAnalysisError(f"Failed to analyze user tone: {str(e)}")
    
    def _analyze_writing_style(self, post_texts: List[str]) -> str:
        """Analyze overall writing style from posts."""
        combined_text = ' '.join(post_texts).lower()
        
        # Calculate style indicators
        formal_indicators = ['furthermore', 'therefore', 'consequently', 'moreover', 'nevertheless']
        casual_indicators = ['hey', 'awesome', 'cool', 'amazing', 'love', 'excited']
        professional_indicators = ['pleased', 'delighted', 'honored', 'grateful', 'appreciate']
        
        formal_score = sum(combined_text.count(word) for word in formal_indicators)
        casual_score = sum(combined_text.count(word) for word in casual_indicators)
        professional_score = sum(combined_text.count(word) for word in professional_indicators)
        
        # Determine dominant style
        if formal_score > casual_score and formal_score > professional_score:
            return "formal"
        elif casual_score > professional_score:
            return "casual"
        else:
            return "professional"
    
    def _analyze_tone(self, post_texts: List[str]) -> str:
        """Analyze emotional tone from posts."""
        combined_text = ' '.join(post_texts).lower()
        
        # Tone indicators
        tone_indicators = {
            'enthusiastic': ['excited', 'thrilled', 'amazing', 'fantastic', 'incredible', 'love'],
            'informative': ['learn', 'understand', 'explain', 'share', 'information', 'knowledge'],
            'inspirational': ['inspire', 'motivate', 'achieve', 'dream', 'goal', 'success'],
            'analytical': ['analyze', 'data', 'research', 'study', 'findings', 'evidence'],
            'conversational': ['think', 'feel', 'believe', 'opinion', 'thoughts', 'experience']
        }
        
        tone_scores = {}
        for tone, indicators in tone_indicators.items():
            tone_scores[tone] = sum(combined_text.count(word) for word in indicators)
        
        # Return dominant tone
        return max(tone_scores, key=tone_scores.get) if tone_scores else "informative"
    
    def _analyze_personality_traits(self, post_texts: List[str]) -> List[str]:
        """Analyze personality traits from posts."""
        combined_text = ' '.join(post_texts).lower()
        
        trait_scores = {}
        for trait, indicators in self.personality_indicators.items():
            trait_scores[trait] = sum(combined_text.count(word) for word in indicators)
        
        # Return top 3 traits
        sorted_traits = sorted(trait_scores.items(), key=lambda x: x[1], reverse=True)
        return [trait for trait, score in sorted_traits[:3] if score > 0]
    
    def _analyze_communication_preferences(self, post_texts: List[str]) -> Dict[str, Any]:
        """Analyze communication preferences from posts."""
        combined_text = ' '.join(post_texts)
        
        # Count emojis
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]')
        emoji_count = len(emoji_pattern.findall(combined_text))
        
        # Count hashtags
        hashtag_count = len(re.findall(r'#\w+', combined_text))
        
        # Analyze post length preferences
        post_lengths = [len(post) for post in post_texts]
        avg_length = sum(post_lengths) / len(post_lengths) if post_lengths else 0
        
        # Analyze call-to-action usage
        cta_patterns = [r'what do you think', r'share your', r'let me know', r'thoughts?', r'comment below']
        cta_count = sum(len(re.findall(pattern, combined_text.lower())) for pattern in cta_patterns)
        
        return {
            "use_emojis": emoji_count > len(post_texts) * 0.3,  # More than 30% of posts have emojis
            "include_hashtags": hashtag_count > 0,
            "max_hashtags": min(10, max(3, hashtag_count // len(post_texts))),
            "preferred_length": "short" if avg_length < 200 else "medium" if avg_length < 500 else "long",
            "call_to_action_style": "direct" if cta_count > len(post_texts) * 0.4 else "subtle",
            "avg_post_length": int(avg_length)
        }
    
    def _analyze_engagement_patterns(self, post_texts: List[str]) -> List[str]:
        """Analyze engagement patterns from posts."""
        combined_text = ' '.join(post_texts).lower()
        
        pattern_scores = {}
        for pattern_name, patterns in self.engagement_patterns.items():
            score = 0
            for pattern in patterns:
                score += len(re.findall(pattern, combined_text))
            pattern_scores[pattern_name] = score
        
        # Return patterns with significant presence
        threshold = len(post_texts) * 0.2  # At least 20% of posts
        return [pattern for pattern, score in pattern_scores.items() if score >= threshold]
    
    def _analyze_vocabulary_level(self, post_texts: List[str]) -> str:
        """Analyze vocabulary sophistication level."""
        combined_text = ' '.join(post_texts).lower()
        
        level_scores = {}
        for level, words in self.professional_indicators.items():
            level_scores[level] = sum(combined_text.count(word) for word in words)
        
        # Determine vocabulary level
        if level_scores.get('high', 0) > level_scores.get('medium', 0):
            return "sophisticated"
        elif level_scores.get('medium', 0) > level_scores.get('low', 0):
            return "professional"
        else:
            return "conversational"
    
    def _analyze_post_structure(self, post_texts: List[str]) -> Dict[str, Any]:
        """Analyze structural patterns in posts."""
        # Analyze paragraph structure
        multi_paragraph_posts = sum(1 for post in post_texts if '\n\n' in post or len(post.split('\n')) > 2)
        
        # Analyze use of lists
        list_posts = sum(1 for post in post_texts if re.search(r'^\d+\.|\n-|\n•', post, re.MULTILINE))
        
        # Analyze question usage
        question_posts = sum(1 for post in post_texts if '?' in post)
        
        return {
            "uses_paragraphs": multi_paragraph_posts > len(post_texts) * 0.3,
            "uses_lists": list_posts > len(post_texts) * 0.2,
            "asks_questions": question_posts > len(post_texts) * 0.4,
            "avg_sentences_per_post": sum(len(re.split(r'[.!?]+', post)) for post in post_texts) / len(post_texts)
        }
    
    async def _extract_industry_focus(self, post_texts: List[str]) -> List[str]:
        """Extract industry focus areas from posts using AI."""
        try:
            # Use AI to identify industry topics
            combined_sample = ' '.join(post_texts[:5])[:2000]  # Sample for analysis
            
            # Simple keyword-based extraction for now
            industry_keywords = {
                'technology': ['tech', 'software', 'ai', 'machine learning', 'data', 'digital'],
                'finance': ['finance', 'investment', 'banking', 'fintech', 'trading', 'market'],
                'healthcare': ['health', 'medical', 'healthcare', 'patient', 'clinical', 'pharma'],
                'education': ['education', 'learning', 'teaching', 'student', 'academic', 'training'],
                'marketing': ['marketing', 'brand', 'advertising', 'campaign', 'social media', 'content'],
                'sales': ['sales', 'selling', 'customer', 'client', 'revenue', 'pipeline'],
                'consulting': ['consulting', 'advisory', 'strategy', 'transformation', 'optimization'],
                'entrepreneurship': ['startup', 'entrepreneur', 'founder', 'venture', 'innovation']
            }
            
            combined_lower = combined_sample.lower()
            industry_scores = {}
            
            for industry, keywords in industry_keywords.items():
                score = sum(combined_lower.count(keyword) for keyword in keywords)
                if score > 0:
                    industry_scores[industry] = score
            
            # Return top industries
            sorted_industries = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)
            return [industry for industry, score in sorted_industries[:3]]
            
        except Exception as e:
            logger.warning(f"Failed to extract industry focus: {str(e)}")
            return []
    
    async def _extract_expertise_areas(self, post_texts: List[str]) -> List[str]:
        """Extract expertise areas from posts."""
        try:
            combined_text = ' '.join(post_texts).lower()
            
            # Common expertise indicators
            expertise_patterns = {
                'leadership': ['lead', 'manage', 'director', 'ceo', 'executive', 'leadership'],
                'project_management': ['project', 'agile', 'scrum', 'planning', 'execution'],
                'data_analysis': ['data', 'analytics', 'insights', 'metrics', 'analysis'],
                'software_development': ['code', 'programming', 'development', 'software', 'engineering'],
                'digital_marketing': ['seo', 'sem', 'social media', 'content marketing', 'digital'],
                'business_strategy': ['strategy', 'planning', 'growth', 'business development'],
                'sales': ['sales', 'selling', 'revenue', 'business development', 'account management'],
                'design': ['design', 'ux', 'ui', 'creative', 'visual', 'branding']
            }
            
            expertise_scores = {}
            for area, keywords in expertise_patterns.items():
                score = sum(combined_text.count(keyword) for keyword in keywords)
                if score > 0:
                    expertise_scores[area] = score
            
            # Return top expertise areas
            sorted_expertise = sorted(expertise_scores.items(), key=lambda x: x[1], reverse=True)
            return [area for area, score in sorted_expertise[:3]]
            
        except Exception as e:
            logger.warning(f"Failed to extract expertise areas: {str(e)}")
            return []
    
    async def _get_default_tone_profile(self, session: AsyncSession, user_id: str) -> ToneProfile:
        """Get default tone profile when insufficient data is available."""
        logger.info(f"Using default tone profile for user {user_id}")
        
        return ToneProfile(
            writing_style="professional",
            tone="informative",
            personality_traits=["analytical", "thoughtful"],
            industry_focus=[],
            expertise_areas=[],
            communication_preferences={
                "use_emojis": False,
                "include_hashtags": True,
                "max_hashtags": 3,
                "call_to_action_style": "subtle",
                "preferred_length": "medium",
                "avg_post_length": 250
            }
        )
    
    async def _save_tone_profile(
        self,
        session: AsyncSession,
        user_id: str,
        tone_profile: ToneProfile,
        analysis_results: Dict[str, Any]
    ):
        """Save analyzed tone profile to user record."""
        try:
            user_repo = UserRepository(session)
            
            # Convert tone profile to dict and add analysis metadata
            tone_data = tone_profile.dict()
            tone_data.update({
                "analysis_metadata": {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "posts_analyzed": len(analysis_results.get('post_structure', {}).get('avg_sentences_per_post', 0)),
                    "vocabulary_level": analysis_results.get('vocabulary_level', 'professional'),
                    "engagement_patterns": analysis_results.get('engagement_patterns', []),
                    "post_structure": analysis_results.get('post_structure', {}),
                    "analysis_version": "1.0"
                }
            })
            
            # Update user's tone profile
            await user_repo.update_tone_profile(user_id, tone_data)
            
            logger.info(f"Tone profile saved for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to save tone profile for user {user_id}: {str(e)}")
    
    async def update_tone_profile_from_feedback(
        self,
        session: AsyncSession,
        user_id: str,
        approved_content: str,
        rejected_content: Optional[str] = None
    ):
        """
        Update tone profile based on user feedback on generated content.
        
        Args:
            session: Database session
            user_id: User ID
            approved_content: Content that user approved
            rejected_content: Content that user rejected
        """
        try:
            logger.info(f"Updating tone profile from feedback for user {user_id}")
            
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            
            if not user or not user.tone_profile:
                logger.warning(f"No existing tone profile found for user {user_id}")
                return
            
            # Analyze approved content for patterns
            if approved_content:
                approved_analysis = self._analyze_single_content(approved_content)
                
                # Update preferences based on approved content
                current_prefs = user.tone_profile.get("communication_preferences", {})
                
                # Adjust emoji usage
                if approved_analysis.get("has_emojis"):
                    current_prefs["use_emojis"] = True
                
                # Adjust hashtag preferences
                hashtag_count = approved_analysis.get("hashtag_count", 0)
                if hashtag_count > 0:
                    current_prefs["max_hashtags"] = max(current_prefs.get("max_hashtags", 3), hashtag_count)
                
                # Update tone profile
                updated_tone = user.tone_profile.copy()
                updated_tone["communication_preferences"] = current_prefs
                updated_tone["last_feedback_update"] = datetime.utcnow().isoformat()
                
                await user_repo.update_tone_profile(user_id, updated_tone)
                
                logger.info(f"Tone profile updated from feedback for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update tone profile from feedback: {str(e)}")
    
    def _analyze_single_content(self, content: str) -> Dict[str, Any]:
        """Analyze a single piece of content for feedback learning."""
        return {
            "has_emojis": bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', content)),
            "hashtag_count": len(re.findall(r'#\w+', content)),
            "length": len(content),
            "has_questions": '?' in content,
            "has_call_to_action": bool(re.search(r'what do you think|share your|let me know|thoughts?', content.lower()))
        }
    
    def get_tone_analysis_summary(self, tone_profile: ToneProfile) -> Dict[str, Any]:
        """
        Generate a human-readable summary of tone analysis.
        
        Args:
            tone_profile: Analyzed tone profile
            
        Returns:
            Dictionary with readable tone analysis summary
        """
        return {
            "writing_style_description": self._get_style_description(tone_profile.writing_style),
            "tone_description": self._get_tone_description(tone_profile.tone),
            "personality_summary": self._get_personality_summary(tone_profile.personality_traits),
            "communication_style": self._get_communication_style(tone_profile.communication_preferences),
            "content_preferences": {
                "emoji_usage": "Uses emojis" if tone_profile.communication_preferences.get("use_emojis") else "Minimal emoji usage",
                "hashtag_style": f"Uses {tone_profile.communication_preferences.get('max_hashtags', 3)} hashtags on average",
                "post_length": tone_profile.communication_preferences.get("preferred_length", "medium").title(),
                "engagement_approach": tone_profile.communication_preferences.get("call_to_action_style", "subtle").title()
            },
            "industry_focus": tone_profile.industry_focus or ["General business"],
            "expertise_areas": tone_profile.expertise_areas or ["Professional development"]
        }
    
    def _get_style_description(self, style: str) -> str:
        """Get description for writing style."""
        descriptions = {
            "professional": "Uses professional language with industry terminology",
            "casual": "Conversational and approachable tone",
            "formal": "Structured and formal communication style"
        }
        return descriptions.get(style, "Professional communication style")
    
    def _get_tone_description(self, tone: str) -> str:
        """Get description for tone."""
        descriptions = {
            "informative": "Focuses on sharing knowledge and insights",
            "enthusiastic": "Energetic and passionate communication",
            "inspirational": "Motivational and uplifting messages",
            "analytical": "Data-driven and logical approach",
            "conversational": "Engaging and discussion-oriented"
        }
        return descriptions.get(tone, "Informative and professional tone")
    
    def _get_personality_summary(self, traits: List[str]) -> str:
        """Get summary of personality traits."""
        if not traits:
            return "Balanced professional personality"
        
        trait_descriptions = {
            "analytical": "data-driven",
            "creative": "innovative",
            "leadership": "leadership-oriented",
            "collaborative": "team-focused",
            "technical": "technically-minded",
            "entrepreneurial": "business-oriented"
        }
        
        described_traits = [trait_descriptions.get(trait, trait) for trait in traits[:3]]
        return f"Demonstrates {', '.join(described_traits)} characteristics"
    
    def _get_communication_style(self, preferences: Dict[str, Any]) -> str:
        """Get communication style description."""
        style_elements = []
        
        if preferences.get("use_emojis"):
            style_elements.append("expressive")
        
        if preferences.get("call_to_action_style") == "direct":
            style_elements.append("engaging")
        
        length_pref = preferences.get("preferred_length", "medium")
        if length_pref == "short":
            style_elements.append("concise")
        elif length_pref == "long":
            style_elements.append("detailed")
        else:
            style_elements.append("balanced")
        
        return f"{', '.join(style_elements).title()} communication style" if style_elements else "Professional communication style"