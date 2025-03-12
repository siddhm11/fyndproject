
# THIS IS TO PERFORM TEH CRUD OPERATIONS 

from fastapi import APIRouter , Depends , HTTPException
# api router allows grouping related API routes nder one router , making it modular and reusable

#Depends is from FastAPI dependency injection system used to inject database access

# httpescpetion  is for Http error responses 

from bson import ObjectId

#objwctid is a mongodb unique identifier for each doc with _id 
# and an ojectid we need to convert string id into onjectid when querying


from app.schemas import MovieCreate,MovieResponse

#we are importinhg the create for the post request and 
# response if for the id along with teh db
from app.database import get_database
#getdb give and returns the MONGODB instance 

router = APIRouter()
#creates a fastapi instance router 

@router.post("/",response_model=MovieResponse)
#this ensures that the response is of the correct model , which is with the id 
async def add_movie(movie:MovieCreate , db = Depends(get_database)):
    #async def is used to define an async function 
    #movie: validates incoming request data during input using moviecreate schema 
    #db= Depends fethces db connection before executing the function 
    
    movie_dict = movie.model_dump()
    result = await db.movies.insert_one(movie_dict)
    return {**movie_dict,"id":str(result.inserted_id)}


@router.get("/",response_model=list[MovieResponse])
async def get_movies(db=Depends(get_database)):
    movies = await db.movies.find().to_list(length = 100)
    
    return [{**movie,"id":str(movie["_id"])} for movie in movies]

@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id:str,db = Depends(get_database)):
    movie = await db.movies.find_one({"_id":ObjectId(movie_id)})
    if not movie:
        raise HTTPException(status_code=404,detail="Movie isn't there in the data base")
    return {**movie,"id":str(movie["_id"])}