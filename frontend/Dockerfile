FROM node:20-alpine
WORKDIR /src
COPY frontend/package.json ./package.json
RUN npm i
COPY frontend/src ./src
ENV VITE_API_URL=https://modular-chat-ai.onrender.com
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]
