# Palm Cash Deployment Guide

Complete guide for deploying Palm Cash to production environments.

## Deployment Options

### 1. PythonAnywhere (Recommended for Beginners)

**Best for**: Quick deployment, minimal setup, free tier available

**Pros**:
- Easy setup (no server management)
- Free tier available
- Built-in MySQL database
- SSL certificate included
- Good for small to medium projects

**Cons**:
- Limited customization
- Resource limits on free tier
- Vendor lock-in

**Guide**: [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md)

**Quick Start**:
```bash
# 1. Create PythonAnywhere account
# 2. Clone repository
# 3. Create virtual environment
# 4. Install dependencies
# 5. Configure database
# 6. Run migrations
# 7. Configure web app
# 8. Reload and access site
```

### 2. AWS (Recommended for Production)

**Best for**: Large-scale, high-traffic applications

**Pros**:
- Highly scalable
- Full control
- Pay-as-you-go pricing
- Global infrastructure

**Cons**:
- More complex setup
- Requires AWS knowledge
- Higher cost

**Services**:
- EC2 (compute)
- RDS (database)
- S3 (static files)
- CloudFront (CDN)

### 3. DigitalOcean (Recommended for Mid-Scale)

**Best for**: Medium-sized applications, good balance of simplicity and control

**Pros**:
- Simple setup
- Affordable pricing
- Good documentation
- App Platform available

**Cons**:
- Less scalable than AWS
- Manual server management

### 4. Heroku (Deprecated)

**Note**: Heroku free tier is no longer available. Consider PythonAnywhere or DigitalOcean instead.

## Pre-Deployment Checklist

Before deploying to any platform:

- [ ] All code committed to GitHub
- [ ] `.env` file NOT in version control
- [ ] `DEBUG=False` in production settings
- [ ] `SECRET_KEY` is unique and strong
- [ ] `ALLOWED_HOSTS` configured
- [ ] Database migrations tested locally
- [ ] Static files collected locally
- [ ] All tests passing
- [ ] Email configuration ready
- [ ] Backup strategy planned

## Environment Variables for Production

```env
# Django
DEBUG=False
SECRET_KEY=your-very-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=palmcash_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=3306

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Site
SITE_URL=https://yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Deployment Steps (General)

### Step 1: Prepare Code

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### Step 2: Set Up Server

- Create account on chosen platform
- Create database
- Create virtual environment
- Install dependencies

### Step 3: Configure Application

- Create `.env` file with production values
- Run migrations
- Create superuser
- Collect static files

### Step 4: Configure Web Server

- Set up WSGI application
- Configure static files serving
- Configure media files serving
- Set up SSL/HTTPS

### Step 5: Deploy

- Deploy application
- Verify deployment
- Monitor for errors

### Step 6: Post-Deployment

- Set up monitoring
- Configure backups
- Set up logging
- Monitor performance

## Monitoring & Maintenance

### Error Monitoring

- Check error logs regularly
- Set up error alerts
- Monitor application performance

### Database Maintenance

- Regular backups
- Monitor database size
- Optimize queries

### Security

- Keep dependencies updated
- Monitor for security vulnerabilities
- Regular security audits
- Monitor access logs

### Performance

- Monitor CPU usage
- Monitor memory usage
- Monitor database performance
- Optimize slow queries

## Scaling

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Upgrade database tier

### Horizontal Scaling
- Add more application servers
- Use load balancer
- Use CDN for static files
- Use caching (Redis)

## Backup Strategy

### Database Backups

```bash
# Manual backup
mysqldump -u user -p database_name > backup.sql

# Automated backups (daily)
# Set up cron job or platform backup service
```

### File Backups

- Backup media files
- Backup static files
- Backup configuration files

### Backup Storage

- Store backups in multiple locations
- Use cloud storage (S3, etc.)
- Test restore process regularly

## Disaster Recovery

### Recovery Plan

1. **Database Recovery**
   - Restore from latest backup
   - Verify data integrity

2. **Application Recovery**
   - Redeploy application
   - Verify all services running

3. **Testing**
   - Test all functionality
   - Verify data consistency

### Recovery Time Objectives (RTO)

- **Critical**: < 1 hour
- **Important**: < 4 hours
- **Non-critical**: < 24 hours

## Cost Optimization

### PythonAnywhere
- Use free tier for development
- Upgrade to paid only when needed
- Monitor CPU usage

### AWS
- Use free tier where possible
- Use spot instances for non-critical workloads
- Use reserved instances for predictable workloads

### DigitalOcean
- Start with smallest droplet
- Scale up as needed
- Use managed databases

## Security Best Practices

1. **Keep Dependencies Updated**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

2. **Use Strong Passwords**
   - Database password: 16+ characters
   - Admin password: 16+ characters
   - App password: 16+ characters

3. **Enable HTTPS**
   - Use SSL certificate
   - Force HTTPS redirect
   - Use secure cookies

4. **Protect Sensitive Data**
   - Use environment variables
   - Don't commit secrets
   - Use secure storage

5. **Monitor Access**
   - Review access logs
   - Monitor failed login attempts
   - Set up alerts

## Troubleshooting

### Application Won't Start

1. Check error logs
2. Verify environment variables
3. Verify database connection
4. Check migrations

### Static Files Not Loading

1. Run `python manage.py collectstatic`
2. Verify static files path
3. Check web server configuration
4. Clear browser cache

### Database Connection Issues

1. Verify database is running
2. Check credentials
3. Verify network connectivity
4. Check firewall rules

### Email Not Sending

1. Verify email credentials
2. Check email configuration
3. Verify SMTP settings
4. Check firewall/port blocking

## Support Resources

- **PythonAnywhere**: https://help.pythonanywhere.com/
- **AWS**: https://aws.amazon.com/support/
- **DigitalOcean**: https://www.digitalocean.com/support/
- **Django**: https://docs.djangoproject.com/
- **Palm Cash**: Check GitHub issues

## Next Steps

1. Choose deployment platform
2. Follow platform-specific guide
3. Deploy application
4. Monitor and maintain
5. Plan for scaling

---

**Ready to deploy?** Start with [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md) for the easiest option!
