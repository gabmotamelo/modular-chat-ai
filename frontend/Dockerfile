FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm i
COPY . .
ENV VITE_API_URL=http://localhost:8080
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]
