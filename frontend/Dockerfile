FROM nginx:alpine

ARG API_KEY_SITE=local-site-key

RUN rm -rf /usr/share/nginx/html/*

COPY . /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN sed -i "s/var API_KEY_SITE = \"local-site-key\";/var API_KEY_SITE = \"${API_KEY_SITE}\";/" \
      /usr/share/nginx/html/cookie-notice.js
