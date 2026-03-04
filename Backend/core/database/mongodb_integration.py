"""
========================
MongoDB Integration for Flask Backend
========================

This module integrates Flask with MongoDB to store game attempts persistently.
Previously, Flask used in-memory storage (struggle_detector.attempt_history)
which was lost on restart. Now all data is stored in MongoDB.

DATA FLOW:
1. Frontend sends userId (MongoDB ObjectId) with game requests
2. Flask receives userId and processes the game attempt
3. Flask saves attempt details to MongoDB GameAttempt collection
4. Flask queries MongoDB for user progress (instead of in-memory data)
5. Analytics endpoints read from MongoDB for accurate reports

BENEFITS:
- Persistent storage: Data survives Flask restarts
- Shared source of truth: Express.js and Flask read same data
- Scalability: Can serve multiple Flask instances
- Integration: Easy to integrate with Express.js dashboard
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import os
from bson.objectid import ObjectId

# ========================
# MONGODB CONNECTION
# ========================

class MongoDBManager:
    """Manages MongoDB connection and operations for game attempts"""
    
    def __init__(self, mongodb_uri=None, db_name="test"):
        """
        Initialize MongoDB connection
        
        Args:
            mongodb_uri: MongoDB connection string (or read from ENV)
            db_name: Database name for game data
        """
        self.mongodb_uri = mongodb_uri or os.getenv(
            'MONGODB_URI',
            'mongodb+srv://dulmiwitharana:uS1LtYnTvcWkmJtU@cluster0.8tb8jax.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0'
        )
        self.db_name = db_name
        self.client = None
        self.db = None
        self.game_attempts = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Verify connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.db_name]
            self.game_attempts = self.db['game_attempts']
            
            # Create indexes for optimal query performance
            self._create_indexes()
            
            print(f"✅ MongoDB Connected: {self.db_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB Connection Error: {e}")
            print(f"⚠️  Falling back to in-memory storage")
            return False
    
    def _create_indexes(self):
        """Create indexes for common queries"""
        try:
            # Index for user queries
            self.game_attempts.create_index([("userId", 1), ("createdAt", -1)])
            # Index for level analysis
            self.game_attempts.create_index([("userId", 1), ("level", 1), ("correct", 1)])
            # Index for word performance
            self.game_attempts.create_index([("userId", 1), ("word", 1)])
            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️  Could not create indexes: {e}")
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB Disconnected")
    
    # ========================
    # CRUD OPERATIONS
    # ========================
    
    def save_game_attempt(self, attempt_data):
        """
        Save a game attempt to MongoDB
        
        Args:
            attempt_data (dict): Game attempt details
                {
                    'userId': str (MongoDB ObjectId),
                    'level': str,
                    'word': str,
                    'sinhalaWord': str,
                    'englishTranslation': str,
                    'correct': bool,
                    'confidence': float (0-100),
                    'timeTaken': float (seconds),
                    'attemptNumber': int,
                    'hintsProvided': list,
                    'feedbackGiven': str,
                    'sessionId': str (optional)
                }
        
        Returns:
            dict: Inserted document with _id
        """
        try:
            # Ensure userId is ObjectId
            if isinstance(attempt_data['userId'], str):
                attempt_data['userId'] = ObjectId(attempt_data['userId'])
            
            # Add timestamps
            attempt_data['createdAt'] = datetime.now()
            attempt_data['updatedAt'] = datetime.now()
            
            # Insert into MongoDB
            result = self.game_attempts.insert_one(attempt_data)
            
            print(f"✅ Saved attempt for user {attempt_data['userId']}: {attempt_data['word']}")
            
            return {
                '_id': str(result.inserted_id),
                **attempt_data
            }
            
        except Exception as e:
            print(f"❌ Error saving game attempt: {e}")
            return None
    
    def get_user_stats(self, user_id):
        """
        Get overall statistics for a user
        
        Args:
            user_id: MongoDB ObjectId as string or ObjectId
        
        Returns:
            dict: User statistics
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            pipeline = [
                {
                    '$match': {'userId': user_id}
                },
                {
                    '$group': {
                        '_id': None,
                        'totalAttempts': {'$sum': 1},
                        'correctAttempts': {
                            '$sum': {'$cond': ['$correct', 1, 0]}
                        },
                        'uniqueWords': {'$addToSet': '$word'},
                        'avgTime': {'$avg': '$timeTaken'},
                        'avgConfidence': {'$avg': '$confidence'},
                        'firstAttempt': {'$min': '$createdAt'},
                        'lastAttempt': {'$max': '$createdAt'}
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'totalAttempts': 1,
                        'correctAttempts': 1,
                        'wordsLearned': {'$size': '$uniqueWords'},
                        'overallAccuracy': {
                            '$multiply': [
                                {'$divide': ['$correctAttempts', '$totalAttempts']},
                                100
                            ]
                        },
                        'avgTime': {'$round': ['$avgTime', 2]},
                        'avgConfidence': {'$round': ['$avgConfidence', 2]},
                        'firstAttempt': 1,
                        'lastAttempt': 1
                    }
                }
            ]
            
            result = list(self.game_attempts.aggregate(pipeline))
            
            if result:
                return result[0]
            else:
                return {
                    'totalAttempts': 0,
                    'correctAttempts': 0,
                    'wordsLearned': 0,
                    'overallAccuracy': 0,
                    'avgTime': 0,
                    'avgConfidence': 0
                }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return None
    
    def get_level_stats(self, user_id, level):
        """
        Get statistics for a specific level
        
        Args:
            user_id: MongoDB ObjectId as string or ObjectId
            level: Level name ('basic', 'easy', 'medium', 'hard')
        
        Returns:
            dict: Level statistics
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            pipeline = [
                {
                    '$match': {
                        'userId': user_id,
                        'level': level
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total': {'$sum': 1},
                        'correct': {'$sum': {'$cond': ['$correct', 1, 0]}},
                        'avgTime': {'$avg': '$timeTaken'},
                        'avgConfidence': {'$avg': '$confidence'}
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'total': 1,
                        'correct': 1,
                        'accuracy': {
                            '$multiply': [
                                {'$divide': ['$correct', '$total']},
                                100
                            ]
                        },
                        'avgTime': {'$round': ['$avgTime', 2]},
                        'avgConfidence': {'$round': ['$avgConfidence', 2]}
                    }
                }
            ]
            
            result = list(self.game_attempts.aggregate(pipeline))
            
            if result:
                return result[0]
            else:
                return {
                    'total': 0,
                    'correct': 0,
                    'accuracy': 0,
                    'avgTime': 0,
                    'avgConfidence': 0
                }
            
        except Exception as e:
            print(f"❌ Error getting level stats: {e}")
            return None
    
    def get_word_stats(self, user_id):
        """
        Get performance statistics for each word
        
        Args:
            user_id: MongoDB ObjectId as string or ObjectId
        
        Returns:
            list: Word statistics
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            pipeline = [
                {
                    '$match': {'userId': user_id}
                },
                {
                    '$group': {
                        '_id': '$word',
                        'sinhalaWord': {'$first': '$sinhalaWord'},
                        'englishTranslation': {'$first': '$englishTranslation'},
                        'level': {'$first': '$level'},
                        'total': {'$sum': 1},
                        'correct': {'$sum': {'$cond': ['$correct', 1, 0]}},
                        'avgTime': {'$avg': '$timeTaken'},
                        'lastAttempt': {'$max': '$createdAt'}
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'word': '$_id',
                        'sinhalaWord': 1,
                        'englishTranslation': 1,
                        'level': 1,
                        'total': 1,
                        'correct': 1,
                        'accuracy': {
                            '$multiply': [
                                {'$divide': ['$correct', '$total']},
                                100
                            ]
                        },
                        'avgTime': {'$round': ['$avgTime', 2]},
                        'lastAttempt': 1
                    }
                },
                {
                    '$sort': {'lastAttempt': -1}
                }
            ]
            
            return list(self.game_attempts.aggregate(pipeline))
            
        except Exception as e:
            print(f"❌ Error getting word stats: {e}")
            return None
    
    def get_recent_attempts(self, user_id, limit=10):
        """
        Get recent game attempts for a user
        
        Args:
            user_id: MongoDB ObjectId as string or ObjectId
            limit: Number of recent attempts to retrieve
        
        Returns:
            list: Recent attempts
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            return list(
                self.game_attempts
                .find({'userId': user_id})
                .sort('createdAt', -1)
                .limit(limit)
            )
            
        except Exception as e:
            print(f"❌ Error getting recent attempts: {e}")
            return None
    
    def get_attempts_by_date_range(self, user_id, start_date, end_date):
        """
        Get attempts within a date range
        
        Args:
            user_id: MongoDB ObjectId as string or ObjectId
            start_date: datetime object
            end_date: datetime object
        
        Returns:
            list: Attempts in date range
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            return list(
                self.game_attempts.find({
                    'userId': user_id,
                    'createdAt': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }).sort('createdAt', -1)
            )
            
        except Exception as e:
            print(f"❌ Error getting attempts by date range: {e}")
            return None
    
    def is_struggling(self, user_id, word, level, threshold=2):
        """
        Detect if user is struggling with a word
        
        Args:
            user_id: MongoDB ObjectId as string or ObjectId
            word: Word being checked
            level: Level of the word
            threshold: Number of failures to consider struggling
        
        Returns:
            bool: True if user is struggling
        """
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            # Get last 5 attempts for this word
            recent_attempts = list(
                self.game_attempts
                .find({
                    'userId': user_id,
                    'word': word,
                    'level': level
                })
                .sort('createdAt', -1)
                .limit(5)
            )
            
            if not recent_attempts:
                return False
            
            wrong_count = sum(1 for a in recent_attempts if not a.get('correct'))
            return wrong_count >= threshold
            
        except Exception as e:
            print(f"❌ Error checking struggle: {e}")
            return False


# ========================
# FALLBACK IN-MEMORY STORAGE
# ========================

class InMemoryAttemptStorage:
    """Fallback storage when MongoDB is unavailable"""
    
    def __init__(self):
        self.attempt_history = {}
    
    def save_game_attempt(self, attempt_data):
        user_id = str(attempt_data.get('userId'))
        if user_id not in self.attempt_history:
            self.attempt_history[user_id] = []
        
        self.attempt_history[user_id].append({
            **attempt_data,
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        })
        
        return attempt_data
    
    def get_user_stats(self, user_id):
        user_id = str(user_id)
        if user_id not in self.attempt_history:
            return {
                'totalAttempts': 0,
                'correctAttempts': 0,
                'wordsLearned': 0,
                'overallAccuracy': 0,
                'avgTime': 0,
                'avgConfidence': 0
            }
        
        attempts = self.attempt_history[user_id]
        correct = sum(1 for a in attempts if a.get('correct'))
        total = len(attempts)
        
        return {
            'totalAttempts': total,
            'correctAttempts': correct,
            'wordsLearned': len(set(a['word'] for a in attempts)),
            'overallAccuracy': (correct / total * 100) if total > 0 else 0,
            'avgTime': sum(a.get('timeTaken', 0) for a in attempts) / total if total > 0 else 0,
            'avgConfidence': sum(a.get('confidence', 0) for a in attempts) / total if total > 0 else 0
        }
    
    def get_level_stats(self, user_id, level):
        user_id = str(user_id)
        if user_id not in self.attempt_history:
            return {'total': 0, 'correct': 0, 'accuracy': 0, 'avgTime': 0, 'avgConfidence': 0}
        
        level_attempts = [a for a in self.attempt_history[user_id] if a.get('level') == level]
        correct = sum(1 for a in level_attempts if a.get('correct'))
        total = len(level_attempts)
        
        return {
            'total': total,
            'correct': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'avgTime': sum(a.get('timeTaken', 0) for a in level_attempts) / total if total > 0 else 0,
            'avgConfidence': sum(a.get('confidence', 0) for a in level_attempts) / total if total > 0 else 0
        }


# ========================
# GLOBAL INSTANCE
# ========================

# Try MongoDB first, fallback to in-memory
mongodb_manager = MongoDBManager()
if not mongodb_manager.connect():
    print("⚠️  Using in-memory fallback storage (data will be lost on restart)")
    mongodb_manager = InMemoryAttemptStorage()
