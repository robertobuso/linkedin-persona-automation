"""
LinkedIn Post Discovery Service for LinkedIn Presence Automation Application.

Phase 1: Extends existing content discovery pipeline to find LinkedIn posts
for commenting opportunities. Integrates with existing EngagementOpportunity
model and recommendation_service.py scoring algorithms.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.deep_content_analysis import DeepContentAnalysisService
from app.services.recommendation_service import RecommendationService
from app.services.linkedin_api_service import LinkedInAPIService
from app.repositories.engagement_repository import EngagementRepository
from app.repositories.user_repository import UserRepository
from app.models.engagement import EngagementOpportunity, EngagementType, EngagementPriority
from app.services.linkedin_oauth_service import LinkedInOAuthService
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class PostDiscoveryResult:
    """Result of post discovery operation."""
    posts_found: int
    opportunities_created: int
    processing_time: float
    discovery_metadata: Dict[str, Any]


@dataclass
class LinkedInPostData:
    """LinkedIn post data structure."""
    post_id: str
    post_url: str
    author_name: str
    author_profile_url: str
    content: str
    published_at: datetime
    engagement_metrics: Dict[str, int]
    company: Optional[str] = None
    industry_tags: List[str] = None


class LinkedInPostDiscoveryService:
    """
    Service for discovering LinkedIn posts suitable for commenting.
    
    Extends existing content discovery pipeline to find engagement opportunities
    using existing scoring algorithms and analytics infrastructure.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.engagement_repo = EngagementRepository(session)
        self.user_repo = UserRepository(session)
        
        # CORRECT way to instantiate LinkedInOAuthService (no arguments)
        self.linkedin_oauth_service_instance = LinkedInOAuthService() 
        
        # Pass the session and the oauth_service instance to LinkedInAPIService
        self.linkedin_api = LinkedInAPIService(
            session=session, 
            oauth_service=self.linkedin_oauth_service_instance
        )
        
        self.content_analysis = DeepContentAnalysisService(session)
        self.recommendation_service = RecommendationService(session)
    
    async def discover_posts_for_commenting(
        self,
        user_id: UUID,
        discovery_config: Optional[Dict[str, Any]] = None
    ) -> PostDiscoveryResult:
        """
        Discover LinkedIn posts for commenting opportunities.
        
        Args:
            user_id: User ID to discover posts for
            discovery_config: Optional configuration for discovery
            
        Returns:
            PostDiscoveryResult with discovery statistics
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting post discovery for user {user_id}")
        
        try:
            # Get user profile and preferences
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.has_valid_linkedin_token():
                logger.warning(f"User {user_id} not found or no valid LinkedIn token")
                return PostDiscoveryResult(0, 0, 0.0, {"error": "Invalid user or token"})
            
            # Set default discovery configuration
            config = self._get_discovery_config(user, discovery_config)
            
            # Discover posts from various sources
            discovered_posts = await self._discover_posts_from_sources(user, config)
            
            # Analyze and score posts for commenting potential
            opportunities_created = 0
            for post_data in discovered_posts:
                try:
                    comment_potential = await self.analyze_comment_potential(
                        post_data, user, config
                    )
                    
                    if comment_potential['should_comment']:
                        opportunity = await self.create_comment_opportunity(
                            user_id, post_data, comment_potential
                        )
                        if opportunity:
                            opportunities_created += 1
                            
                except Exception as e:
                    logger.warning(f"Failed to analyze post {post_data.post_id}: {str(e)}")
                    continue
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = PostDiscoveryResult(
                posts_found=len(discovered_posts),
                opportunities_created=opportunities_created,
                processing_time=processing_time,
                discovery_metadata={
                    "user_id": str(user_id),
                    "discovery_sources": config.get("sources", []),
                    "max_posts_analyzed": config.get("max_posts", 50),
                    "min_engagement_threshold": config.get("min_engagement", 5),
                    "discovery_timestamp": start_time.isoformat()
                }
            )
            
            logger.info(f"Post discovery completed: {result.posts_found} posts, "
                       f"{result.opportunities_created} opportunities")
            return result
            
        except Exception as e:
            logger.error(f"Post discovery failed for user {user_id}: {str(e)}")
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return PostDiscoveryResult(
                0, 0, processing_time, 
                {"error": str(e), "discovery_timestamp": start_time.isoformat()}
            )
    
    async def analyze_comment_potential(
        self,
        post_data: LinkedInPostData,
        user: User,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a post's potential for commenting using existing scoring patterns.
        
        Args:
            post_data: LinkedIn post data
            user: User profile for personalization
            config: Discovery configuration
            
        Returns:
            Dictionary with commenting potential analysis
        """
        try:
            # Use existing content analysis patterns
            analysis_factors = {
                'relevance_score': 0.0,
                'engagement_potential': 0.0,
                'timing_score': 0.0,
                'relationship_score': 0.0,
                'should_comment': False,
                'reasoning': [],
                'suggested_approach': 'thoughtful'
            }
            
            # 1. Analyze content relevance using existing patterns
            relevance_score = await self._calculate_content_relevance(post_data, user)
            analysis_factors['relevance_score'] = relevance_score
            
            if relevance_score >= config.get('min_relevance_score', 0.6):
                analysis_factors['reasoning'].append(f"High content relevance ({relevance_score:.2f})")
            
            # 2. Analyze engagement potential using existing predictor patterns
            engagement_score = self._calculate_engagement_potential(post_data, config)
            analysis_factors['engagement_potential'] = engagement_score
            
            if engagement_score >= config.get('min_engagement_potential', 0.5):
                analysis_factors['reasoning'].append(f"Good engagement potential ({engagement_score:.2f})")
            
            # 3. Analyze timing using existing scheduling patterns
            timing_score = self._calculate_timing_score(post_data)
            analysis_factors['timing_score'] = timing_score
            
            if timing_score >= 0.7:
                analysis_factors['reasoning'].append("Optimal timing for engagement")
            
            # 4. Analyze relationship/network connection
            relationship_score = await self._calculate_relationship_score(post_data, user)
            analysis_factors['relationship_score'] = relationship_score
            
            if relationship_score >= 0.6:
                analysis_factors['reasoning'].append("Strong network connection")
            
            # 5. Determine overall commenting recommendation
            composite_score = (
                relevance_score * 0.35 +
                engagement_score * 0.25 +
                timing_score * 0.20 +
                relationship_score * 0.20
            )
            
            # Apply user-specific thresholds
            comment_threshold = config.get('comment_threshold', 0.65)
            analysis_factors['should_comment'] = composite_score >= comment_threshold
            
            if analysis_factors['should_comment']:
                # Determine suggested commenting approach
                if relevance_score > 0.8:
                    analysis_factors['suggested_approach'] = 'expert_insight'
                elif engagement_score > 0.8:
                    analysis_factors['suggested_approach'] = 'engaging_question'
                elif relationship_score > 0.8:
                    analysis_factors['suggested_approach'] = 'supportive'
                else:
                    analysis_factors['suggested_approach'] = 'thoughtful'
            
            analysis_factors['composite_score'] = composite_score
            return analysis_factors
            
        except Exception as e:
            logger.error(f"Failed to analyze comment potential: {str(e)}")
            return {
                'relevance_score': 0.0,
                'engagement_potential': 0.0,
                'timing_score': 0.0,
                'relationship_score': 0.0,
                'should_comment': False,
                'reasoning': [f"Analysis failed: {str(e)}"],
                'suggested_approach': 'thoughtful',
                'composite_score': 0.0
            }
    
    async def create_comment_opportunity(
        self,
        user_id: UUID,
        post_data: LinkedInPostData,
        comment_potential: Dict[str, Any]
    ) -> Optional[EngagementOpportunity]:
        """
        Create EngagementOpportunity record using existing patterns.
        
        Args:
            user_id: User ID
            post_data: LinkedIn post data
            comment_potential: Comment potential analysis
            
        Returns:
            Created EngagementOpportunity or None if failed
        """
        try:
            # Determine priority based on composite score
            composite_score = comment_potential.get('composite_score', 0.0)
            if composite_score >= 0.85:
                priority = EngagementPriority.URGENT
            elif composite_score >= 0.75:
                priority = EngagementPriority.HIGH
            elif composite_score >= 0.65:
                priority = EngagementPriority.MEDIUM
            else:
                priority = EngagementPriority.LOW
            
            # Set expiration (posts become less relevant over time)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Create opportunity using existing repository patterns
            opportunity = await self.engagement_repo.create_opportunity(
                user_id=user_id,
                target_type="linkedin_post",
                target_url=post_data.post_url,
                target_id=post_data.post_id,
                target_author=post_data.author_name,
                target_title=f"Post by {post_data.author_name}",
                target_content=post_data.content[:500],  # Truncate for storage
                target_company=post_data.company,
                engagement_type=EngagementType.COMMENT,
                priority=priority,
                engagement_reason="; ".join(comment_potential.get('reasoning', [])),
                context_tags=[
                    comment_potential.get('suggested_approach', 'thoughtful'),
                    "linkedin_post",
                    "auto_discovered"
                ] + (post_data.industry_tags or []),
                relevance_score=int(comment_potential.get('relevance_score', 0.5) * 100),
                engagement_potential=int(comment_potential.get('engagement_potential', 0.5) * 100),
                ai_analysis={
                    "comment_potential": comment_potential,
                    "post_metrics": post_data.engagement_metrics,
                    "discovery_timestamp": datetime.utcnow().isoformat(),
                    "suggested_approach": comment_potential.get('suggested_approach'),
                    "composite_score": composite_score
                },
                expires_at=expires_at,
                discovery_source="linkedin_post_discovery",
                discovery_metadata={
                    "author_profile": post_data.author_profile_url,
                    "post_published_at": post_data.published_at.isoformat(),
                    "engagement_metrics": post_data.engagement_metrics
                }
            )
            
            logger.debug(f"Created comment opportunity {opportunity.id} for post {post_data.post_id}")
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to create comment opportunity: {str(e)}")
            return None
    
    async def _discover_posts_from_sources(
        self,
        user: User,
        config: Dict[str, Any]
    ) -> List[LinkedInPostData]:
        """Discover posts from various LinkedIn sources."""
        discovered_posts = []
        max_posts = config.get('max_posts', 50)
        
        try:
            # Source 1: User's LinkedIn feed
            if 'feed' in config.get('sources', ['feed']):
                feed_posts = await self._discover_from_feed(user, max_posts // 2)
                discovered_posts.extend(feed_posts)
            
            # Source 2: Network activity (connections' posts)
            if 'network' in config.get('sources', ['feed']):
                network_posts = await self._discover_from_network(user, max_posts // 4)
                discovered_posts.extend(network_posts)
            
            # Source 3: Industry hashtags and topics
            if 'industry' in config.get('sources', ['feed']):
                industry_posts = await self._discover_from_industry_topics(user, max_posts // 4)
                discovered_posts.extend(industry_posts)
            
            # Remove duplicates and limit results
            unique_posts = {post.post_id: post for post in discovered_posts}
            return list(unique_posts.values())[:max_posts]
            
        except Exception as e:
            logger.error(f"Failed to discover posts from sources: {str(e)}")
            return []
    
    async def _discover_from_feed(self, user: User, limit: int) -> List[LinkedInPostData]:
        """Discover posts from user's LinkedIn feed."""
        try:
            # Use existing LinkedIn API service patterns
            feed_posts = await self.linkedin_api.get_user_posts(user, count=limit)
            
            discovered = []
            for post_data in feed_posts:
                try:
                    linkedin_post = self._parse_linkedin_post(post_data)
                    if linkedin_post:
                        discovered.append(linkedin_post)
                except Exception as e:
                    logger.warning(f"Failed to parse feed post: {str(e)}")
                    continue
            
            return discovered
            
        except Exception as e:
            logger.error(f"Failed to discover from feed: {str(e)}")
            return []
    
    async def _discover_from_network(self, user: User, limit: int) -> List[LinkedInPostData]:
        """Discover posts from user's network connections."""
        # This would require additional LinkedIn API calls
        # For now, return empty list as placeholder
        logger.info("Network post discovery not yet implemented")
        return []
    
    async def _discover_from_industry_topics(self, user: User, limit: int) -> List[LinkedInPostData]:
        """Discover posts from industry topics and hashtags."""
        # This would require LinkedIn content discovery API
        # For now, return empty list as placeholder
        logger.info("Industry topic discovery not yet implemented")
        return []
    
    def _parse_linkedin_post(self, api_post_data: Dict[str, Any]) -> Optional[LinkedInPostData]:
        """Parse LinkedIn API post data into LinkedInPostData structure."""
        try:
            # Extract basic post information
            post_id = api_post_data.get('id', '')
            if not post_id:
                return None
            
            # Parse post content
            content = ""
            specific_content = api_post_data.get('specificContent', {})
            if 'com.linkedin.ugc.ShareContent' in specific_content:
                share_content = specific_content['com.linkedin.ugc.ShareContent']
                commentary = share_content.get('shareCommentary', {})
                content = commentary.get('text', '')
            
            # Parse author information
            author_urn = api_post_data.get('author', '')
            author_name = "Unknown Author"  # Would need additional API call to resolve
            author_profile_url = f"https://linkedin.com/in/{author_urn.split(':')[-1]}"
            
            # Parse timestamps
            created_time = api_post_data.get('created', {}).get('time', 0)
            published_at = datetime.fromtimestamp(created_time / 1000) if created_time else datetime.utcnow()
            
            # Mock engagement metrics (would come from separate API calls)
            engagement_metrics = {
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'views': 0
            }
            
            return LinkedInPostData(
                post_id=post_id,
                post_url=f"https://linkedin.com/feed/update/{post_id}",
                author_name=author_name,
                author_profile_url=author_profile_url,
                content=content,
                published_at=published_at,
                engagement_metrics=engagement_metrics,
                company=None,  # Would need additional resolution
                industry_tags=[]  # Would need content analysis
            )
            
        except Exception as e:
            logger.error(f"Failed to parse LinkedIn post: {str(e)}")
            return None
    
    async def _calculate_content_relevance(
        self,
        post_data: LinkedInPostData,
        user: User
    ) -> float:
        """Calculate content relevance using existing analysis patterns."""
        try:
            # Use existing content preferences patterns
            user_interests = user.get_interests_for_llm()
            post_content = post_data.content.lower()
            
            # Simple keyword matching (could be enhanced with LLM analysis)
            relevance_indicators = user_interests.lower().split()
            matches = sum(1 for indicator in relevance_indicators if indicator in post_content)
            
            # Normalize to 0-1 scale
            max_possible_matches = len(relevance_indicators)
            if max_possible_matches == 0:
                return 0.5  # Default relevance
            
            base_relevance = matches / max_possible_matches
            
            # Boost for certain content types
            if any(keyword in post_content for keyword in ['insight', 'tip', 'learn', 'experience']):
                base_relevance += 0.1
            
            return min(1.0, base_relevance)
            
        except Exception as e:
            logger.warning(f"Failed to calculate content relevance: {str(e)}")
            return 0.5
    
    def _calculate_engagement_potential(
        self,
        post_data: LinkedInPostData,
        config: Dict[str, Any]
    ) -> float:
        """Calculate engagement potential using existing predictor patterns."""
        try:
            base_score = 0.5
            
            # Factor 1: Post age (newer posts have higher potential)
            post_age_hours = (datetime.utcnow() - post_data.published_at).total_seconds() / 3600
            if post_age_hours <= 2:
                age_factor = 1.0
            elif post_age_hours <= 6:
                age_factor = 0.8
            elif post_age_hours <= 24:
                age_factor = 0.6
            else:
                age_factor = 0.3
            
            # Factor 2: Content characteristics
            content_factor = 0.5
            content_lower = post_data.content.lower()
            
            if '?' in post_data.content:  # Questions encourage engagement
                content_factor += 0.2
            if any(word in content_lower for word in ['what', 'how', 'why', 'thoughts']):
                content_factor += 0.1
            if len(post_data.content) > 100:  # Substantial content
                content_factor += 0.1
            
            # Factor 3: Current engagement momentum
            current_engagement = sum(post_data.engagement_metrics.values())
            if current_engagement >= config.get('min_engagement', 5):
                momentum_factor = min(1.0, current_engagement / 20)  # Cap at 20 engagements
            else:
                momentum_factor = 0.2
            
            # Combine factors
            engagement_potential = (
                base_score * 0.3 +
                age_factor * 0.3 +
                content_factor * 0.2 +
                momentum_factor * 0.2
            )
            
            return min(1.0, engagement_potential)
            
        except Exception as e:
            logger.warning(f"Failed to calculate engagement potential: {str(e)}")
            return 0.5
    
    def _calculate_timing_score(self, post_data: LinkedInPostData) -> float:
        """Calculate timing score for commenting."""
        try:
            now = datetime.utcnow()
            post_age_hours = (now - post_data.published_at).total_seconds() / 3600
            
            # Optimal commenting window: 1-6 hours after posting
            if 1 <= post_age_hours <= 6:
                return 1.0
            elif post_age_hours <= 1:
                return 0.7  # Too early
            elif post_age_hours <= 12:
                return 0.8
            elif post_age_hours <= 24:
                return 0.6
            else:
                return 0.3  # Too old
                
        except Exception as e:
            logger.warning(f"Failed to calculate timing score: {str(e)}")
            return 0.5
    
    async def _calculate_relationship_score(
        self,
        post_data: LinkedInPostData,
        user: User
    ) -> float:
        """Calculate relationship/network connection score."""
        try:
            # This would require LinkedIn network API calls
            # For now, return moderate score based on heuristics
            
            base_score = 0.5
            
            # Boost for certain author characteristics
            author_name = post_data.author_name.lower()
            if any(title in author_name for title in ['ceo', 'founder', 'director', 'manager']):
                base_score += 0.2
            
            # Company connection (if available)
            if post_data.company:
                # Could check if user works at same company or partner companies
                base_score += 0.1
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.warning(f"Failed to calculate relationship score: {str(e)}")
            return 0.5
    
    def _get_discovery_config(
        self,
        user: User,
        custom_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get discovery configuration from user preferences and custom config."""
        # Default configuration
        default_config = {
            'sources': ['feed'],  # Available: feed, network, industry
            'max_posts': 50,
            'min_relevance_score': 0.6,
            'min_engagement_potential': 0.5,
            'min_engagement': 5,
            'comment_threshold': 0.65,
            'max_opportunities_per_run': 20
        }
        
        # Merge with user preferences
        user_prefs = user.preferences or {}
        commenting_prefs = user_prefs.get('commenting_preferences', {})
        default_config.update(commenting_prefs)
        
        # Apply custom configuration
        if custom_config:
            default_config.update(custom_config)
        
        return default_config