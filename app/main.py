from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # configurations , changes, and 

from app.api.endpoints import auth, users, projects, bugs, comments
from app.db.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bugzilla Lite API",
        description="Backend API for Bugzilla Lite bug tracking system",
        version="1.0.0"
    )
    
    # CORS middleware Configuration: This middleware is responsible for handling Cross-Origin Resource Sharing (CORS) in our API. 
    # CORS is a security feature implemented by web browsers that restricts web pages from making requests to a different domain than the one that served the web page. 
    # In this configuration, we are allowing all origins, methods, and headers for simplicity, but in a production environment, you would typically restrict these settings to enhance security.
    '''
    Front-end security rule that filters out responses from the backend before they can be displayed by the browser.
    This is important for preventing unauthorized access and ensuring that only trusted sources can interact with our API


    Alternatives: 
    * If your front-end and backend domains are the same, you don't need to worry about CORS. 
      However, if they are different (e.g., frontend on localhost:3000 and backend on localhost:8000), you need to configure CORS to allow the frontend to access the backend API.
    
    * Use a reverse proxy (very common in production)
        Example setup:
        Browser → Nginx → Backend
        Frontend and API appear under same domain
        Nginx routes internally

    
    '''
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],    # allow all origins for simplicity, can be restricted in production
        allow_credentials=True, # allow cookies and authentication headers

        # The following 2 cannot be true at the same time. 
        # Because it would allow any website to make requests to our API with any HTTP method and any headers, which can be a security risk.
        # In production, you should specify allowed origins, methods, and headers to enhance security.
        # allow_origins=["*"],    # allow all origins for simplicity, can be restricted in production
        # allow_credentials=True, # allow cookies and authentication headers


        allow_methods=["*"],
        allow_headers=["*"],    # allow all methods and headers for simplicity, can be restricted in production
        #max_age=3600        # cache preflight response for 1 hour
        #expose_headers=["X-Total-Count"]    # expose custom headers to the client (e.g., for pagination). Allows frontend JavaScript to read certain response headers.
    )
    
    # Include routers
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(projects.router)
    app.include_router(bugs.router)
    app.include_router(comments.router)
    
    @app.on_event("startup")
    def startup_event():
        init_db()
    
    @app.get("/")
    def root():
        return {"message": "Bugzilla Lite API", "version": "1.0.0"}
    
    @app.get("/health")
    def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()


