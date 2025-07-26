import { useEffect, useState } from "react";
import { getAllFiles } from "../services";
import MenuItem from "@mui/material/MenuItem";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import FormControl from "@mui/material/FormControl";

function RecentUploads({ updateUploadedFile, rerender }) {
  let [files, setFiles] = useState(null);
  let [selectedFile, setSelectedFile] = useState("Recent Uploads");

  useEffect(() => {
    setSelectedFile(rerender ? rerender.file_id : "Recent Uploads");
    getAllFiles()
      .then((response) => {
        setFiles(
          response.data.files.filter(
            (file) => !file.file_id.startsWith("batch")
          )
        );
      })
      .catch((error) => {
        console.log(error);
        setFiles([]);
      });
  }, [rerender]);

  const handleChange = (event) => {
    setSelectedFile(event.target.value);
    const selectedFile = files.find((f) => f.file_id === event.target.value);
    updateUploadedFile(event.target.value, selectedFile.original_filename);
  };
  return (
    files && (
      <>
        <FormControl
          variant="filled"
          sx={{
            m: 1,
            minWidth: "40%",
            backgroundColor: "whitesmoke",
            borderRadius: "0.5rem",
          }}
        >
          <InputLabel
            id="recentUploads"
            sx={{
              color: "gray",
              "&.Mui-focused": {
                color: "gray",
              },
            }}
          >
            Recent Uploads
          </InputLabel>
          <Select
            sx={{
              backgroundColor: "whitesmoke",
              borderRadius: "0.5rem",
            }}
            value={selectedFile}
            labelId="recentUploads"
            onChange={handleChange}
          >
            <MenuItem value="Recent Uploads" disabled>
              {/* <em>None</em> */}
            </MenuItem>
            {files &&
              files.length != 0 &&
              files.map((file) => {
                return (
                  <MenuItem value={file.file_id}>
                    {file.original_filename}
                  </MenuItem>
                );
              })}
          </Select>
        </FormControl>
      </>
    )
  );
}

export default RecentUploads;
