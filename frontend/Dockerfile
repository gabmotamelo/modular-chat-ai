FROM node:20-alpine
WORKDIR /app
COPY package.json ./
# handle no lock file gracefully
RUN npm i
COPY . .
ENV VITE_API_URL=http://localhost:8080
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]
