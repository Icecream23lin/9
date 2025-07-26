import axios from "axios";

const port = localStorage.getItem("WIL_BACKEND_PORT");

export const upload_file = (file) => {
  let formData = new FormData();
  formData.append("file", file);

  return axios.post(`http://localhost:${port}/api/upload`, formData, {
    headers: {
      Accept: "application/json",
    },
  });
};

export const upload_files = (files) => {
  let formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  return axios.post(`http://localhost:${port}/api/upload/batch`, formData, {
    headers: {
      Accept: "application/json",
    },
  });
};

export const getAllFiles = () => {
  return axios.get(`http://localhost:${port}/api/upload/files`, {
    headers: {
      Accept: "application/json",
    },
  });
};

export const getReport = (file_id) => {
  return axios.post(`http://localhost:${port}/api/report/generate/${file_id}`, {
    headers: {
      Accept: "application/json",
    },
  });
};

export const getReportBatch = (file_ids) => {
  return axios.post(
    `http://localhost:${port}/api/report/generate/`,
    {
      file_ids: file_ids,
      report_title: "Year on Year Comparison",
    },
    {
      headers: {
        Accept: "application/json",
      },
    }
  );
};

export const getAllVisualisation = (analysis_id) => {
  return axios.get(`http://localhost:${port}/api/download/${analysis_id}`, {
    responseType: "blob",
    headers: {
      Accept: "application/json",
    },
  });
};

export const getPdfUrl = (url) => {
  return `http://localhost:${port}${url}`;
};
