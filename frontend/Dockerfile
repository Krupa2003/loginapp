# Use Nginx as the base image
FROM nginx:alpine

# Copy the HTML files into the Nginx directory
COPY ./templates /usr/share/nginx/html

# Copy the static assets (CSS, JS, images) into the Nginx static directory
COPY ./static /usr/share/nginx/html/static

# Expose the port on which Nginx serves
EXPOSE 80
