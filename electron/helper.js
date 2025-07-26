const http = require("http");

async function checkBackend(url) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      const isSuccess = res.statusCode >= 200 && res.statusCode < 300;
      resolve(isSuccess);
      res.destroy();
    });

    req.on("error", () => resolve(false));
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function retryWithDelay(fn, retries, delay) {
  for (let i = 0; i < retries; i++) {
    if (await fn()) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, delay));
  }
  return false;
}

module.exports = { checkBackend, retryWithDelay };
