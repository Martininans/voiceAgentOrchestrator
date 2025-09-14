# SSL Certificates Directory

This directory contains SSL certificates for production deployment.

## Required Files

For production deployment, you need to place the following files in this directory:

- `cert.pem` - SSL certificate file
- `key.pem` - SSL private key file
- `chain.pem` - SSL certificate chain file (optional)

## How to Obtain SSL Certificates

### Option 1: Let's Encrypt (Recommended for production)
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to this directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### Option 2: Self-signed certificates (Development only)
```bash
# Generate self-signed certificate (DO NOT USE IN PRODUCTION)
openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes
```

### Option 3: Commercial SSL Provider
- Purchase SSL certificate from providers like DigiCert, Comodo, etc.
- Download certificate files and place them in this directory

## Security Notes

- Never commit actual certificate files to version control
- Keep private keys secure and restrict access
- Use strong encryption (RSA 2048+ or ECDSA)
- Regularly renew certificates before expiration

## Docker Volume Mounting

The certificates are mounted as volumes in docker-compose.prod.yml:

```yaml
volumes:
  - ./nginx/ssl:/etc/nginx/ssl:ro
```

This makes the certificates available to the nginx container at `/etc/nginx/ssl/`.


