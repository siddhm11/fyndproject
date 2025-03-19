# Movie Database API 

This documentation provides details on the movie database API, including endpoints, authentication, and usage examples.

## Overview

The Movie Database API is a RESTful service that allows users to search, create, update, and retrieve movie information. The API requires authentication for most endpoints, with certain operations restricted to admin users.

## Base URL

The API is hosted at: `https://fyndproject0011.onrender.com`

## Authentication

The API uses JWT (JSON Web Token) authentication. 

### Obtaining a Token

To access protected endpoints, you need to obtain an authentication token:

```
POST /token
```

**Request Body:**
```
username=<username>&password=<password>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Usage:**
Include the token in the Authorization header for subsequent requests:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Root Endpoint

```
GET /
```

**Description:** Test endpoint to verify API is running.

**Authentication:** None required

**Response:**
```json
{
  "message": "API is running! Connect to /movies/ to see data."
}
```

### 2. User Information

```
GET /users/me
```

**Description:** Retrieve current user information.

**Authentication:** Required

**Response:**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "disabled": false,
  "role": "admin"
}
```

### 3. Movie Management

#### 3.1 Get All Movies

```
GET /movies/
```

**Description:** Retrieve all movies or search for specific movies.

**Authentication:** Optional

**Query Parameters:**
- `search` (optional): Text to search for in movie titles, genres, or directors

**Response:**
```json
[
  {
    "id": "60c72b2d8f4a7e001c123456",
    "title": "The Shawshank Redemption",
    "year": 1994,
    "genre": "Drama",
    "director": "Frank Darabont",
    "cast": ["Tim Robbins", "Morgan Freeman"],
    "rating": 9.3,
    "description": "Two imprisoned men bond over a number of years..."
  },
  // More movies...
]
```

#### 3.2 Get Movie by ID

```
GET /movies/{movie_id}
```

**Description:** Retrieve a specific movie by its ID.

**Authentication:** Optional

**Path Parameters:**
- `movie_id`: The ID of the movie to retrieve

**Response:**
```json
{
  "id": "60c72b2d8f4a7e001c123456",
  "title": "The Shawshank Redemption",
  "year": 1994,
  "genre": "Drama",
  "director": "Frank Darabont",
  "cast": ["Tim Robbins", "Morgan Freeman"],
  "rating": 9.3,
  "description": "Two imprisoned men bond over a number of years..."
}
```

#### 3.3 Create Movie

```
POST /movies/
```

**Description:** Create a new movie (admin only).

**Authentication:** Required (admin)

**Request Body:**
```json
{
  "title": "Inception",
  "year": 2010,
  "genre": "Sci-Fi, Action",
  "director": "Christopher Nolan",
  "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Ellen Page"],
  "rating": 8.8,
  "description": "A thief who steals corporate secrets through dream-sharing technology..."
}
```

**Response:**
```json
{
  "id": "60c72b2d8f4a7e001c123457",
  "title": "Inception",
  "year": 2010,
  "genre": "Sci-Fi, Action",
  "director": "Christopher Nolan",
  "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Ellen Page"],
  "rating": 8.8,
  "description": "A thief who steals corporate secrets through dream-sharing technology..."
}
```

#### 3.4 Update Movie

```
PUT /movies/{movie_id}
```

**Description:** Update an existing movie (admin only).

**Authentication:** Required (admin)

**Path Parameters:**
- `movie_id`: The ID of the movie to update

**Request Body:**
```json
{
  "title": "Inception",
  "year": 2010,
  "genre": "Sci-Fi, Action, Thriller",
  "director": "Christopher Nolan",
  "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
  "rating": 8.8,
  "description": "A thief who steals corporate secrets through dream-sharing technology..."
}
```

**Response:**
```json
{
  "id": "60c72b2d8f4a7e001c123457",
  "title": "Inception",
  "year": 2010,
  "genre": "Sci-Fi, Action, Thriller",
  "director": "Christopher Nolan",
  "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
  "rating": 8.8,
  "description": "A thief who steals corporate secrets through dream-sharing technology..."
}
```

### 4. User Management

#### 4.1 Register User

```
POST /register/
```

**Description:** Register a new user (admin only).

**Authentication:** Required (admin)

**Query Parameters:**
- `username`: Username for the new user
- `password`: Password for the new user
- `email`: Email address for the new user

**Response:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "disabled": false,
  "role": "user"
}
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request (e.g., missing parameters)
- `401 Unauthorized`: Authentication required or invalid credentials
- `403 Forbidden`: The user doesn't have permission (admin required)
- `404 Not Found`: The requested resource doesn't exist
- `500 Internal Server Error`: Server-side error

Error responses include a detail message explaining the error:

```json
{
  "detail": "Incorrect username or password"
}
```

## Test Cases

### 1. Authentication Tests

#### 1.1 Successful Login

**Request:**
```
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Expected Response:**
- Status Code: 200
- Response contains access_token and token_type

#### 1.2 Failed Login - Wrong Password

**Request:**
```
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=wrongpassword
```

**Expected Response:**
- Status Code: 400
- Response contains error detail

### 2. Movie Retrieval Tests

#### 2.1 Get All Movies

**Request:**
```
GET /movies/
```

**Expected Response:**
- Status Code: 200
- Response contains array of movie objects

#### 2.2 Search Movies

**Request:**
```
GET /movies/?search=action
```

**Expected Response:**
- Status Code: 200
- Response contains array of movies matching the search term "action"

#### 2.3 Get Movie by ID

**Request:**
```
GET /movies/{valid_movie_id}
```

**Expected Response:**
- Status Code: 200
- Response contains movie details

#### 2.4 Get Movie with Invalid ID

**Request:**
```
GET /movies/invalidid
```

**Expected Response:**
- Status Code: 404 or 500 (depending on ID format)
- Response contains error detail

### 3. Admin Operation Tests

#### 3.1 Create Movie (Admin)

**Request:**
```
POST /movies/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "title": "Test Movie",
  "year": 2023,
  "genre": "Test",
  "director": "Test Director",
  "cast": ["Actor 1", "Actor 2"],
  "rating": 8.0,
  "description": "Test description"
}
```

**Expected Response:**
- Status Code: 200
- Response contains created movie with ID

#### 3.2 Create Movie (Non-Admin)

**Request:**
```
POST /movies/
Authorization: Bearer {user_token}
Content-Type: application/json

{
  "title": "Test Movie",
  "year": 2023,
  "genre": "Test",
  "director": "Test Director",
  "cast": ["Actor 1", "Actor 2"],
  "rating": 8.0,
  "description": "Test description"
}
```

**Expected Response:**
- Status Code: 403
- Response contains error detail about admin access required

#### 3.3 Update Movie (Admin)

**Request:**
```
PUT /movies/{valid_movie_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "title": "Updated Test Movie",
  "year": 2023,
  "genre": "Test",
  "director": "Test Director",
  "cast": ["Actor 1", "Actor 2"],
  "rating": 8.5,
  "description": "Updated test description"
}
```

**Expected Response:**
- Status Code: 200
- Response contains updated movie details

#### 3.4 Register New User (Admin)

**Request:**
```
POST /register/?username=testuser&password=testpassword&email=test@example.com
Authorization: Bearer {admin_token}
```

**Expected Response:**
- Status Code: 200
- Response contains created user details (excluding password)

## Using the API with cURL

Here are examples of how to use the API with cURL:

### Login and Get Token

```bash
curl -X POST https://fyndproject0011.onrender.com/token \
  -d "username=admin&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

### Get All Movies

```bash
curl -X GET https://fyndproject0011.onrender.com/movies/
```

### Search Movies

```bash
curl -X GET "https://fyndproject0011.onrender.com/movies/?search=action"
```

### Create Movie (Admin)

```bash
curl -X POST https://fyndproject0011.onrender.com/movies/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Movie",
    "year": 2023,
    "genre": "Action",
    "director": "Director Name",
    "cast": ["Actor 1", "Actor 2"],
    "rating": 8.5,
    "description": "Movie description"
  }'
```

### Update Movie (Admin)

```bash
curl -X PUT https://fyndproject0011.onrender.com/movies/MOVIE_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Movie",
    "year": 2023,
    "genre": "Action",
    "director": "Director Name",
    "cast": ["Actor 1", "Actor 2"],
    "rating": 8.5,
    "description": "Updated description"
  }'
```

## Using the API with JavaScript

Here's an example of how to use the API with JavaScript fetch:

```javascript
// Login and get token
async function login(username, password) {
  const response = await fetch('https://fyndproject0011.onrender.com/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
  });
  
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status}`);
  }
  
  const data = await response.json();
  return data.access_token;
}

// Get all movies
async function getMovies(token = null) {
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch('https://fyndproject0011.onrender.com/movies/', {
    headers
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch movies: ${response.status}`);
  }
  
  return await response.json();
}

// Example usage
async function example() {
  try {
    const token = await login('admin', 'admin123');
    console.log('Token:', token);
    
    const movies = await getMovies(token);
    console.log('Movies:', movies);
  } catch (error) {
    console.error('Error:', error);
  }
}

example();
```

## Development Setup

To set up this project for development:

1. Clone the repository
2. Install backend dependencies:
   ```
   pip install -r api/requirements.txt
   ```
3. Set up environment variables:
   ```
   SECRET_KEY=your_secret_key
   MONGODB_URL=your_mongodb_connection_string
   ```
4. Create an admin user using the provided script:
   ```
   cd backend
   python create_admin.py
   ```
5. Import sample data (optional):
   ```
   cd backend
   python import_data.py
   ```
6. Start the backend server:
   ```
   cd backend
   uvicorn main:app --reload
   ```
7. Open the frontend/index.html file in a browser to access the UI

## Security Considerations

- The API uses JWT for authentication with a configurable expiration time (default: 30 minutes)
- Passwords are hashed using bcrypt before storage
- Role-based access control is implemented for admin operations
- Cross-Origin Resource Sharing (CORS) is enabled for frontend integration
