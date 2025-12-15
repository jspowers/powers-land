# powers.land

Personal website for James Powers featuring professional bio, project showcase, and Texas native landscaping information.

## Overview

This is a modular Flask application built with a blueprint architecture, designed for easy expansion with future projects and features. The site features a **minimal, professional single-page design** inspired by clean portfolio sites, emphasizing professional background over side projects.

The site currently includes:

- **Homepage**: Clean single-page layout with:
  - Professional hero section with contact links
  - About section highlighting data engineering expertise
  - Experience timeline (Databricks, Meta, Deloitte)
  - Technical skills showcase
  - Certifications
  - Dense layout optimized for minimal scrolling
- **About Page**: Extended background and professional journey
- **Texas Native Landscaping Section** (accessible via Projects link):
  - Overview of native plant benefits
  - Plant resources (structure ready for content)
  - Yard design showcase
  - Future: Interactive plant database

## Design Philosophy

The site follows a **minimal, professional aesthetic** with these key principles:

- **Professional-First**: Career background and expertise take center stage
- **Single-Page Efficiency**: Dense layout using Bulma columns to minimize scrolling
- **Monochromatic Color Scheme**: Clean grays and blues with subtle accent colors
- **Mobile-Responsive**: Optimized breakpoints for tablet and mobile viewing
- **Side Projects Secondary**: Landscaping and future projects accessible via simple navigation

## Tech Stack

- **Framework**: Flask 3.0.0 with Application Factory pattern
- **Database**: SQLite (future-ready schema for plant database)
- **Frontend**: Bulma CSS 1.0.4 (mobile-responsive, minimal custom CSS)
- **Deployment**: AWS EC2 with Terraform IaC
- **CI/CD**: GitHub Actions for automated deployment
- **Server**: Gunicorn + Nginx
- **SSL**: Let's Encrypt

## Project Structure

```
powers-land/
├── app/
│   ├── blueprints/          # Modular feature blueprints
│   │   ├── main/            # Homepage and about
│   │   └── landscaping/     # Texas native landscaping
│   ├── models/              # Database models
│   ├── static/              # CSS, JS, images
│   ├── templates/           # Jinja2 templates
│   └── utils/               # Helper functions
├── tests/                   # pytest tests
├── terraform/               # AWS infrastructure
├── .github/workflows/       # CI/CD pipelines
├── config.py                # Environment configurations
└── wsgi.py                  # WSGI entry point
```

## Local Development Setup

### Prerequisites

- Python 3.11
- pip and venv
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd powers-land
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY
   ```

5. **Initialize database**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the development server**:
   ```bash
   flask run
   # or
   python wsgi.py
   ```

7. **Access the application**:
   Open browser to `http://localhost:5000`

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/integration/test_routes.py -v

# Run with coverage
pytest tests/ --cov=app
```

## AWS Deployment (Fully Automated with Terraform)

### Prerequisites

1. **AWS Account** with credentials configured (`aws configure`)
2. **SSH Key Pair** created in AWS Console and saved locally
3. **Route 53 Hosted Zone** for your domain
4. **Terraform** installed (`brew install terraform` on macOS)

### Quick Deploy (Everything Automated!)

```bash
# 1. Navigate to terraform directory
cd terraform

# 2. Create your variables file
cp terraform.tfvars.example terraform.tfvars

# 3. Edit with your values
# - Get your IP: curl ifconfig.me
# - Generate secret: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# - Add your email for SSL notifications

# 4. Deploy everything!
terraform init
terraform apply
```

**That's it!** Terraform automatically:
- ✅ Creates EC2 instance with Ubuntu 24.04
- ✅ Assigns static Elastic IP
- ✅ Configures security groups
- ✅ Sets up Route 53 DNS records
- ✅ Clones your repository
- ✅ Installs all dependencies
- ✅ Runs database migrations
- ✅ Configures Gunicorn + Nginx
- ✅ Obtains Let's Encrypt SSL certificate
- ✅ Starts all services

After ~5 minutes, your site is live at `https://powers.land`!

### Destroying and Recreating

To tear down everything:
```bash
terraform destroy
```

To rebuild from scratch:
```bash
terraform apply  # Uses latest code from GitHub
```

See [terraform/README.md](terraform/README.md) for detailed documentation.

## GitHub Actions CI/CD

### Setup

1. **Create GitHub repository secrets** (Settings → Secrets → Actions):
   - `EC2_HOST`: Elastic IP or domain name
   - `EC2_SSH_KEY`: Contents of your SSH private key (.pem file)

2. **Push to main branch**:
   ```bash
   git push origin main
   ```

3. **Monitor deployment**:
   - Go to Actions tab in GitHub repository
   - Watch the test and deploy jobs

### Workflow

- **On push to main**: Tests run, then auto-deploy to EC2
- **Manual trigger**: Use "Run workflow" button in Actions tab

## Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

## Adding New Projects/Blueprints

1. **Create blueprint directory**:
   ```bash
   mkdir -p app/blueprints/project_name/templates
   ```

2. **Create blueprint files**:
   - `__init__.py`: Blueprint registration
   - `routes.py`: Route handlers
   - `models.py`: Database models (if needed)
   - `templates/`: Jinja2 templates

3. **Register in application factory** (`app/__init__.py`):
   ```python
   from app.blueprints.project_name import project_bp
   app.register_blueprint(project_bp, url_prefix='/project')
   ```

4. **Add to navbar** (`app/templates/components/navbar.html`)

## Future Enhancements

### Landscaping Section Roadmap

- **Phase 2**: Populate plant database with 50-100 Texas native plants
- **Phase 3**: Build interactive plant browsing with filtering
- **Phase 4**: "My Yard" tracking feature for personal plant logs
- **Phase 5**: Care log tracking and maintenance history
- **Phase 6**: REST API for plant data

### Other Potential Projects

- Blog/articles section
- Photo gallery
- Resume/CV showcase
- API playground
- Data visualization projects

## Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Monitor Logs

```bash
# Application logs
sudo journalctl -u powers-land -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### SSL Certificate Renewal

Certbot auto-renews. Test with:
```bash
sudo certbot renew --dry-run
```

## Security Best Practices

- Never commit `.env` or `terraform.tfvars` to version control
- Keep dependencies updated
- SSH access restricted to specific IP (configured in Terraform)
- HTTPS enforced in production
- CSRF protection enabled
- Secure session cookies in production

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

Personal project - All rights reserved

## Contact

- **GitHub**: [jspowers](https://github.com/jspowers)
- **LinkedIn**: [jamesspowers](https://www.linkedin.com/in/jamesspowers/)
- **Website**: [powers.land](https://powers.land)

---

Built with Flask and Bulma CSS
