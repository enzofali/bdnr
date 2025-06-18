## Example Queries

### **1. User Ratings with Movie Details**

This shows how to get user profiles with their rated movies' full details:


```
("User Ratings with Movie Details", lambda: list(db.command('aggregate', 'users', pipeline=[
    {"$match": {"userId": {"$in": list(selected_users[:5])}}},# Sample users{"$lookup": {
        "from": "movies",
        "localField": "ratings.movieId",# Join on movie IDs from ratings"foreignField": "movieId",
        "as": "ratedMovies"
    }},
    {"$project": {
        "userId": 1,
        "ratedMovies": {
            "$map": {
                "input": "$ratedMovies",
                "as": "movie",
                "in": {
                    "title": "$$movie.title",
                    "year": "$$movie.year",
                    "genres": "$$movie.genres",
                    "avgRating": "$$movie.stats.avgRating"
                }
            }
        },
        "ratingCount": {"$size": "$ratings"}
    }},
    {"$limit": 5}
])))
```

### **2. Movies with Their Top Raters**

This finds movies with the users who gave them the highest ratings:


```
("Movies with Top Raters", lambda: list(db.command('aggregate', 'movies', pipeline=[
    {"$match": {"stats.ratingCount": {"$gt": 50}}},# Popular movies{"$lookup": {
        "from": "users",
        "let": {"movie_id": "$movieId"},
        "pipeline": [
            {"$unwind": "$ratings"},
            {"$match": {
                "$expr": {
                    "$and": [
                        {"$eq": ["$ratings.movieId", "$$movie_id"]},
                        {"$gte": ["$ratings.rating", 4.5]}# High ratings]
                }
            }},
            {"$project": {
                "userId": 1,
                "rating": "$ratings.rating",
                "timestamp": "$ratings.timestamp"
            }}
        ],
        "as": "highScorers"
    }},
    {"$match": {"highScorers.0": {"$exists": True}}},# Has at least one high scorer{"$project": {
        "title": 1,
        "year": 1,
        "avgRating": "$stats.avgRating",
        "highScorers": {
            "$slice": [
                {"$sortArray": {
                    "input": "$highScorers",
                    "sortBy": {"rating": -1}
                }},
                5# Top 5 raters]
        }
    }},
    {"$limit": 5}
])))
```

### **3. Genre-Based User Preferences**

This analyzes which genres users rate most highly:

```
("User Genre Preferences", lambda: list(db.command('aggregate', 'users', pipeline=[
    {"$match": {"stats.ratingCount": {"$gt": 20}}},# Active users{"$lookup": {
        "from": "movies",
        "localField": "ratings.movieId",
        "foreignField": "movieId",
        "as": "ratedMovies"
    }},
    {"$unwind": "$ratedMovies"},
    {"$unwind": "$ratedMovies.genres"},
    {"$group": {
        "_id": {
            "userId": "$userId",
            "genre": "$ratedMovies.genres"
        },
        "avgRating": {"$avg": {
            "$arrayElemAt": [
                {"$filter": {
                    "input": "$ratings",
                    "as": "r",
                    "cond": {"$eq": ["$$r.movieId", "$ratedMovies.movieId"]}
                }},
                0
            ]
        }}
    }},
    {"$group": {
        "_id": "$_id.userId",
        "preferredGenres": {
            "$push": {
                "genre": "$_id.genre",
                "avgRating": "$avgRating"
            }
        },
        "count": {"$sum": 1}
    }},
    {"$project": {
        "userId": "$_id",
        "preferredGenres": {
            "$slice": [
                {"$sortArray": {
                    "input": "$preferredGenres",
                    "sortBy": {"avgRating": -1}
                }},
                3# Top 3 genres]
        }
    }},
    {"$limit": 5}
])))
```