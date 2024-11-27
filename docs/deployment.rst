==========
Deployment
==========

This guide covers deploying StreamlitChat in various environments.

Local Deployment
---------------

1. Create a virtual environment::

    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

2. Install the package::

    pip install streamlitchat

3. Run the application::

    streamlit run your_app.py

Docker Deployment
---------------

1. Build the Docker image::

    docker build -t streamlitchat .

2. Run the container::

    docker run -p 8501:8501 streamlitchat

Cloud Deployment
--------------

Streamlit Cloud
~~~~~~~~~~~~~~

1. Push your code to GitHub
2. Log in to share.streamlit.io
3. Deploy from your GitHub repository

Heroku
~~~~~~

1. Create a Procfile::

    web: streamlit run your_app.py

2. Deploy using Heroku CLI::

    heroku create
    git push heroku main

Environment Variables
-------------------

Set these required environment variables:

- ``OPENAI_API_KEY``: Your OpenAI API key
- ``STREAMLIT_SERVER_PORT``: Port for the Streamlit server
- ``STREAMLIT_SERVER_ADDRESS``: Server address (default: 0.0.0.0)

Security Considerations
---------------------

1. Always use environment variables for sensitive data
2. Enable HTTPS in production
3. Implement rate limiting
4. Monitor usage and costs
5. Regular security updates

Performance Tuning
----------------

1. Enable caching for API responses
2. Optimize message history size
3. Configure proper logging levels
4. Use appropriate instance sizes 