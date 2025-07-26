import FileUploadZone from "../Components/FileUploadZone";
import { MyBox } from "../Components/MotionComponents";
import { upload_file, upload_files } from "../services";
import { useState } from "react";
import CustomButton from "../Components/CustomButton";
import RecentUploads from "../Components/RecentUploads";
import UploadAlerts from "../Components/UploadAlerts.jsx";
import UploadListItem from "../Components/UploadListItem.jsx";

function YoYUploadPage() {
  let [successfulUpdate, setSuccessfulUpdate] = useState(false);
  let [errorflag, setErrorflag] = useState(false);
  let [errorMessage, setErrorMessage] = useState("");
  let [uploadedFiles, setUploadedFiles] = useState([]);

  const onClose = () => {
    setErrorflag(false);
    setSuccessfulUpdate(false);
  };

  const handleSingleFileAccepted = (acceptedFile) => {
    upload_file(acceptedFile)
      .then((response) => {
        setSuccessfulUpdate(true);
        setErrorflag(false);
        setUploadedFiles([
          ...uploadedFiles,
          {
            file_id: response.data.file_id,
            original_filename: response.data.original_filename,
          },
        ]);
      })
      .catch((error) => {
        console.log(error);
        setSuccessfulUpdate(false);
        setErrorflag(true);
        setErrorMessage(error.response.data.error);
      });
  };

  const handleDoubleFileAccepted = (acceptedFiles) => {
    upload_files(acceptedFiles)
      .then((response) => {
        setSuccessfulUpdate(true);
        setErrorflag(false);
        setUploadedFiles(
          response.data.results.map(({ file_id, original_filename }) => ({
            file_id,
            original_filename,
          }))
        );
      })
      .catch((error) => {
        console.log(error);
        setSuccessfulUpdate(false);
        setErrorflag(true);
        setErrorMessage(error.response.data.error);
      });
  };
  const handleFilesAccepted = (acceptedFiles) => {
    setErrorflag(false);
    setSuccessfulUpdate(false);
    if (uploadedFiles.length == 2) {
      setSuccessfulUpdate(false);
      setErrorflag(true);
      setErrorMessage("Maximum number of files chosen for comparison");
      return;
    }
    if (acceptedFiles.length == 0) {
      setSuccessfulUpdate(false);
      setErrorflag(true);
      setErrorMessage(
        "Invalid file type, please upload .csv, .xlsx, or .xls files only"
      );
    } else if (acceptedFiles.length == 1) {
      handleSingleFileAccepted(acceptedFiles[0]);
    } else {
      handleDoubleFileAccepted(acceptedFiles);
    }
  };
  return (
    <>
      <MyBox
        id="uploadbox"
        sx={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-evenly",
          alignItems: "center",
          width: "100%",
          height: "40%",
          overflow: "hidden",
        }}
      >
        <FileUploadZone
          onFilesAccepted={handleFilesAccepted}
          maxFiles={uploadedFiles ? 2 - uploadedFiles.length : 2}
        ></FileUploadZone>
      </MyBox>
      <MyBox
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          width: "100%",
        }}
      >
        <UploadAlerts
          successfulUpdate={successfulUpdate}
          errorflag={errorflag}
          errorMessage={errorMessage}
          onClose={onClose}
        />
      </MyBox>
      <MyBox
        sx={{
          display: "flex",
          width: "90%",
          margin: "5%",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {uploadedFiles && uploadedFiles.length !== 0 && (
          <>
            {uploadedFiles.map((file, index) => (
              <UploadListItem
                key={file.file_id || index}
                uploadedFile={file}
                onClick={() => {
                  setUploadedFiles((prev) =>
                    prev.filter((_, i) => i !== index)
                  );
                }}
              />
            ))}
          </>
        )}
      </MyBox>
      <MyBox
        sx={{ display: "flex", justifyContent: "center" }}
        transition={{ duration: 1 }}
      >
        <CustomButton
          disabled={uploadedFiles ? uploadedFiles.length != 2 : false}
          title={"Generate report"}
          navigateTo={"/report/display"}
          state={{
            uploadedFiles: uploadedFiles,
          }}
        ></CustomButton>
      </MyBox>
    </>
  );
}

export default YoYUploadPage;
