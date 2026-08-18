FROM nginx:alpine

ARG API_KEY_SITE=local-site-key

RUN rm -rf /usr/share/nginx/html/*

# Только публичные файлы сайта. COPY . кладёт в webroot nginx.conf и служебное.
COPY index.html team.html mockup.html styles.css cookie-notice.js /usr/share/nginx/html/
COPY legal/ /usr/share/nginx/html/legal/
COPY avatars/ /usr/share/nginx/html/avatars/
COPY assets/ /usr/share/nginx/html/assets/
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN sed -i "s/var API_KEY_SITE = \"local-site-key\";/var API_KEY_SITE = \"${API_KEY_SITE}\";/" \
      /usr/share/nginx/html/cookie-notice.js
