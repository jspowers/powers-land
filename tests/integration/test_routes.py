def test_homepage_loads(client):
    """Test that homepage loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'James Powers' in response.data


def test_homepage_experience_section(client):
    """Test that homepage contains experience section"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Experience' in response.data
    assert b'Meta' in response.data
    assert b'Deloitte' in response.data


def test_homepage_skills_section(client):
    """Test that homepage contains skills section"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Technical Skills' in response.data
    assert b'SQL' in response.data
    assert b'Python' in response.data
    assert b'Apache Airflow' in response.data


def test_homepage_certifications_section(client):
    """Test that homepage contains certifications section"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Certifications' in response.data
    assert b'Databricks Certified Data Engineer Associate' in response.data


def test_about_page_loads(client):
    """Test that about page loads successfully"""
    response = client.get('/about')
    assert response.status_code == 200


def test_landscaping_index_loads(client):
    """Test that landscaping index loads successfully"""
    response = client.get('/landscaping/')
    assert response.status_code == 200
    assert b'Texas Native Landscaping' in response.data


def test_landscaping_resources_loads(client):
    """Test that landscaping resources page loads successfully"""
    response = client.get('/landscaping/resources')
    assert response.status_code == 200


def test_404_error_handler(client):
    """Test that 404 error handler works"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'404' in response.data
