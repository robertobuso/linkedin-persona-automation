"""
Engagement predictor service for LinkedIn Presence Automation Application.

Predicts post engagement using historical performance data and machine learning
models with feature extraction and confidence scoring.
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.content_repository import PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import PostDraft, DraftStatus
from app.models.user import User
from app.schemas.recommendation_schemas import EngagementPrediction

logger = logging.getLogger(__name__)


@dataclass
class PostFeatures:
    """Features extracted from a post for prediction."""
    content_length: int
    hashtag_count: int
    has_question: bool
    has_call_to_action: bool
    has_emoji: bool
    has_url: bool
    word_count: int
    sentence_count: int
    hour_of_day: int
    day_of_week: int
    topic_category: str
    
    def to_vector(self) -> List[float]:
        """Convert features to numerical vector."""
        return [
            float(self.content_length),
            float(self.hashtag_count),
            float(self.has_question),
            float(self.has_call_to_action),
            float(self.has_emoji),
            float(self.has_url),
            float(self.word_count),
            float(self.sentence_count),
            float(self.hour_of_day),
            float(self.day_of_week)
        ]


class SimpleLinearRegression:
    """Simple linear regression model for engagement prediction."""
    
    def __init__(self):
        """Initialize the regression model."""
        self.weights = None
        self.bias = 0.0
        self.is_trained = False
    
    def fit(self, X: List[List[float]], y: List[float]) -> None:
        """
        Train the model on feature vectors and target values.
        
        Args:
            X: Feature vectors
            y: Target engagement values
        """
        if not X or not y or len(X) != len(y):
            logger.warning("Invalid training data for regression model")
            return
        
        try:
            # Convert to numpy arrays
            X_array = np.array(X)
            y_array = np.array(y)
            
            # Add bias term
            X_with_bias = np.column_stack([np.ones(len(X)), X_array])
            
            # Solve normal equation: theta = (X^T * X)^-1 * X^T * y
            XTX = np.dot(X_with_bias.T, X_with_bias)
            XTy = np.dot(X_with_bias.T, y_array)
            
            # Add regularization to prevent overfitting
            regularization = 0.01 * np.eye(XTX.shape[0])
            theta = np.linalg.solve(XTX + regularization, XTy)
            
            self.bias = theta[0]
            self.weights = theta[1:]
            self.is_trained = True
            
            logger.info(f"Model trained with {len(X)} samples")
            
        except Exception as e:
            logger.error(f"Failed to train regression model: {str(e)}")
            self.is_trained = False
    
    def predict(self, X: List[float]) -> float:
        """
        Predict engagement for feature vector.
        
        Args:
            X: Feature vector
            
        Returns:
            Predicted engagement value
        """
        if not self.is_trained or self.weights is None:
            return 0.1  # Default prediction
        
        try:
            prediction = self.bias + np.dot(self.weights, X)
            return max(0.0, float(prediction))  # Ensure non-negative
        except Exception as e:
            logger.warning(f"Prediction failed: {str(e)}")
            return 0.1


class EngagementPredictor:
    """
    Service for predicting post engagement using machine learning.
    
    Uses historical post performance to train models and predict engagement
    for new posts with confidence scoring.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize engagement predictor.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.post_repo = PostDraftRepository(session)
        self.user_repo = UserRepository(session)
        
        # Model cache by user
        self._user_models: Dict[str, SimpleLinearRegression] = {}
        self._model_last_trained: Dict[str, datetime] = {}
        
        # Global baseline model
        self._baseline_model = SimpleLinearRegression()
        self._baseline_last_trained: Optional[datetime] = None
    
    async def predict_engagement(
        self,
        draft: PostDraft,
        user_profile: User
    ) -> EngagementPrediction:
        """
        Predict engagement for a post draft.
        
        Args:
            draft: Post draft to predict engagement for
            user_profile: User profile for personalization
            
        Returns:
            EngagementPrediction with predicted metrics and confidence
        """
        try:
            logger.info(f"Predicting engagement for draft {draft.id}")
            
            # Extract features from the draft
            features = await self._extract_post_features(draft)
            
            # Get or train user-specific model
            user_model = await self._get_user_model(user_profile.id)
            
            # Make prediction
            if user_model and user_model.is_trained:
                predicted_engagement_rate = user_model.predict(features.to_vector())
                confidence = 0.8  # Higher confidence for user-specific model
            else:
                # Fall back to baseline model
                baseline_model = await self._get_baseline_model()
                predicted_engagement_rate = baseline_model.predict(features.to_vector())
                confidence = 0.5  # Lower confidence for baseline
            
            # Calculate specific metrics based on engagement rate
            predicted_metrics = self._calculate_predicted_metrics(
                predicted_engagement_rate, user_profile
            )
            
            return EngagementPrediction(
                predicted_engagement_rate=predicted_engagement_rate,
                predicted_likes=predicted_metrics['likes'],
                predicted_comments=predicted_metrics['comments'],
                predicted_shares=predicted_metrics['shares'],
                predicted_views=predicted_metrics['views'],
                confidence=confidence,
                features_used=features.__dict__,
                model_type='user_specific' if user_model and user_model.is_trained else 'baseline',
                predicted_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Engagement prediction failed: {str(e)}")
            # Return default prediction
            return EngagementPrediction(
                predicted_engagement_rate=0.1,
                predicted_likes=10,
                predicted_comments=2,
                predicted_shares=1,
                predicted_views=100,
                confidence=0.3,
                features_used={},
                model_type='default',
                predicted_at=datetime.utcnow()
            )
    
    async def train_user_model(self, user_id: UUID) -> bool:
        """
        Train user-specific engagement prediction model.
        
        Args:
            user_id: User ID to train model for
            
        Returns:
            True if training was successful
        """
        try:
            logger.info(f"Training engagement model for user {user_id}")
            
            # Get user's historical posts
            historical_posts = await self._get_user_historical_posts(user_id)
            
            if len(historical_posts) < 5:
                logger.warning(f"Insufficient data for user {user_id}: {len(historical_posts)} posts")
                return False
            
            # Extract features and targets
            features = []
            targets = []
            
            for post in historical_posts:
                try:
                    post_features = await self._extract_post_features(post)
                    engagement_rate = self._calculate_actual_engagement_rate(post)
                    
                    if engagement_rate is not None:
                        features.append(post_features.to_vector())
                        targets.append(engagement_rate)
                        
                except Exception as e:
                    logger.warning(f"Failed to process post {post.id}: {str(e)}")
                    continue
            
            if len(features) < 5:
                logger.warning(f"Insufficient valid features for user {user_id}: {len(features)}")
                return False
            
            # Train model
            model = SimpleLinearRegression()
            model.fit(features, targets)
            
            if model.is_trained:
                self._user_models[str(user_id)] = model
                self._model_last_trained[str(user_id)] = datetime.utcnow()
                logger.info(f"Successfully trained model for user {user_id} with {len(features)} samples")
                return True
            else:
                logger.warning(f"Model training failed for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to train user model: {str(e)}")
            return False
    
    async def _extract_post_features(self, draft: PostDraft) -> PostFeatures:
        """Extract features from a post draft."""
        content = draft.content or ""
        hashtags = draft.hashtags or []
        
        # Basic text features
        content_length = len(content)
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # Content analysis
        has_question = '?' in content
        has_call_to_action = any(phrase in content.lower() for phrase in [
            'what do you think', 'share your', 'let me know', 'comment below',
            'thoughts?', 'agree?', 'disagree?'
        ])
        has_emoji = any(ord(char) > 127 for char in content)  # Simple emoji detection
        has_url = 'http' in content or 'www.' in content
        
        # Timing features (use current time if not scheduled)
        if draft.scheduled_for:
            hour_of_day = draft.scheduled_for.hour
            day_of_week = draft.scheduled_for.weekday()
        else:
            now = datetime.utcnow()
            hour_of_day = now.hour
            day_of_week = now.weekday()
        
        # Topic category (simplified)
        topic_category = self._extract_topic_category(content)
        
        return PostFeatures(
            content_length=content_length,
            hashtag_count=len(hashtags),
            has_question=has_question,
            has_call_to_action=has_call_to_action,
            has_emoji=has_emoji,
            has_url=has_url,
            word_count=word_count,
            sentence_count=sentence_count,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            topic_category=topic_category
        )
    
    def _extract_topic_category(self, content: str) -> str:
        """Extract topic category from content."""
        content_lower = content.lower()
        
        # Simple keyword-based categorization
        categories = {
            'technology': ['tech', 'ai', 'software', 'digital', 'data', 'algorithm'],
            'business': ['business', 'strategy', 'growth', 'revenue', 'market'],
            'leadership': ['leadership', 'management', 'team', 'culture', 'vision'],
            'career': ['career', 'job', 'interview', 'skills', 'development'],
            'personal': ['personal', 'life', 'experience', 'story', 'journey']
        }
        
        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _calculate_actual_engagement_rate(self, post: PostDraft) -> Optional[float]:
        """Calculate actual engagement rate from post metrics."""
        if not post.engagement_metrics:
            return None
        
        metrics = post.engagement_metrics
        views = metrics.get('views', 0)
        
        if views == 0:
            return None
        
        total_engagement = (
            metrics.get('likes', 0) +
            metrics.get('comments', 0) +
            metrics.get('shares', 0)
        )
        
        return total_engagement / views
    
    def _calculate_predicted_metrics(
        self,
        engagement_rate: float,
        user_profile: User
    ) -> Dict[str, int]:
        """Calculate specific predicted metrics from engagement rate."""
        # Get user's average reach or use default
        user_prefs = user_profile.preferences or {}
        avg_reach = user_prefs.get('avg_reach', 100)  # Default reach
        
        # Calculate predicted views based on user's typical reach
        predicted_views = max(10, int(avg_reach * (1 + engagement_rate)))
        
        # Calculate engagement breakdown
        total_engagement = int(predicted_views * engagement_rate)
        
        # Typical LinkedIn engagement distribution
        predicted_likes = int(total_engagement * 0.7)  # 70% likes
        predicted_comments = int(total_engagement * 0.2)  # 20% comments
        predicted_shares = int(total_engagement * 0.1)  # 10% shares
        
        return {
            'views': predicted_views,
            'likes': predicted_likes,
            'comments': predicted_comments,
            'shares': predicted_shares
        }
    
    async def _get_user_model(self, user_id: UUID) -> Optional[SimpleLinearRegression]:
        """Get or train user-specific model."""
        user_key = str(user_id)
        
        # Check if we have a recent model
        if (user_key in self._user_models and 
            user_key in self._model_last_trained):
            
            last_trained = self._model_last_trained[user_key]
            if datetime.utcnow() - last_trained < timedelta(days=7):
                return self._user_models[user_key]
        
        # Train new model
        success = await self.train_user_model(user_id)
        if success:
            return self._user_models.get(user_key)
        
        return None
    
    async def _get_baseline_model(self) -> SimpleLinearRegression:
        """Get or train baseline model using all users' data."""
        # Check if we have a recent baseline model
        if (self._baseline_last_trained and 
            datetime.utcnow() - self._baseline_last_trained < timedelta(days=30)):
            return self._baseline_model
        
        # Train new baseline model
        await self._train_baseline_model()
        return self._baseline_model
    
    async def _train_baseline_model(self) -> None:
        """Train baseline model using aggregated data from all users."""
        try:
            logger.info("Training baseline engagement model")
            
            # Get sample of posts from multiple users
            all_posts = await self._get_sample_posts_all_users(limit=200)
            
            if len(all_posts) < 20:
                logger.warning("Insufficient data for baseline model")
                return
            
            # Extract features and targets
            features = []
            targets = []
            
            for post in all_posts:
                try:
                    post_features = await self._extract_post_features(post)
                    engagement_rate = self._calculate_actual_engagement_rate(post)
                    
                    if engagement_rate is not None:
                        features.append(post_features.to_vector())
                        targets.append(engagement_rate)
                        
                except Exception as e:
                    logger.warning(f"Failed to process post {post.id}: {str(e)}")
                    continue
            
            if len(features) >= 20:
                self._baseline_model.fit(features, targets)
                self._baseline_last_trained = datetime.utcnow()
                logger.info(f"Baseline model trained with {len(features)} samples")
            else:
                logger.warning("Insufficient valid features for baseline model")
                
        except Exception as e:
            logger.error(f"Failed to train baseline model: {str(e)}")
    
    async def _get_user_historical_posts(self, user_id: UUID, limit: int = 50) -> List[PostDraft]:
        """Get user's historical published posts with engagement data."""
        try:
            # Get published posts with engagement metrics
            posts = await self.post_repo.get_recent_published_drafts(
                user_id=user_id,
                days=90,  # Last 90 days
                limit=limit
            )
            
            # Filter posts with engagement data
            posts_with_engagement = [
                post for post in posts 
                if post.engagement_metrics and post.engagement_metrics.get('views', 0) > 0
            ]
            
            return posts_with_engagement
            
        except Exception as e:
            logger.error(f"Failed to get user historical posts: {str(e)}")
            return []
    
    async def _get_sample_posts_all_users(self, limit: int = 200) -> List[PostDraft]:
        """Get sample of posts from all users for baseline training."""
        try:
            # Get recent published posts across all users
            stmt = (
                self.session.query(PostDraft)
                .filter(
                    PostDraft.status == DraftStatus.PUBLISHED,
                    PostDraft.published_at >= datetime.utcnow() - timedelta(days=60),
                    PostDraft.engagement_metrics.isnot(None)
                )
                .order_by(PostDraft.published_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get sample posts: {str(e)}")
            return []
    
    async def get_prediction_accuracy(self, user_id: UUID) -> Dict[str, Any]:
        """
        Calculate prediction accuracy for user's model.
        
        Args:
            user_id: User ID to calculate accuracy for
            
        Returns:
            Dictionary with accuracy metrics
        """
        try:
            # Get recent posts with both predictions and actual results
            recent_posts = await self._get_user_historical_posts(user_id, limit=20)
            
            if len(recent_posts) < 5:
                return {
                    'accuracy': 0.0,
                    'sample_size': len(recent_posts),
                    'error': 'Insufficient data for accuracy calculation'
                }
            
            # Calculate prediction errors
            errors = []
            for post in recent_posts:
                try:
                    # Get actual engagement rate
                    actual_rate = self._calculate_actual_engagement_rate(post)
                    if actual_rate is None:
                        continue
                    
                    # Get predicted engagement rate (simulate prediction)
                    features = await self._extract_post_features(post)
                    user_model = await self._get_user_model(user_id)
                    
                    if user_model and user_model.is_trained:
                        predicted_rate = user_model.predict(features.to_vector())
                    else:
                        baseline_model = await self._get_baseline_model()
                        predicted_rate = baseline_model.predict(features.to_vector())
                    
                    # Calculate absolute percentage error
                    if actual_rate > 0:
                        error = abs(predicted_rate - actual_rate) / actual_rate
                        errors.append(error)
                        
                except Exception as e:
                    logger.warning(f"Failed to calculate error for post {post.id}: {str(e)}")
                    continue
            
            if not errors:
                return {
                    'accuracy': 0.0,
                    'sample_size': 0,
                    'error': 'No valid predictions to evaluate'
                }
            
            # Calculate mean absolute percentage error
            mape = sum(errors) / len(errors)
            accuracy = max(0.0, 1.0 - mape)  # Convert error to accuracy
            
            return {
                'accuracy': accuracy,
                'sample_size': len(errors),
                'mean_absolute_percentage_error': mape,
                'model_type': 'user_specific' if str(user_id) in self._user_models else 'baseline'
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate prediction accuracy: {str(e)}")
            return {
                'accuracy': 0.0,
                'sample_size': 0,
                'error': str(e)
            }