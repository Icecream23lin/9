import FileUploadZone from "../Components/FileUploadZone.jsx";
import { MyBox } from "../Components/MotionComponents.js";
import { upload_file, upload_files } from "../services.js";
import { useState } from "react";
import CustomButton from "../Components/CustomButton.jsx";
import RecentUploads from "../Components/RecentUploads.jsx";
import UploadAlerts from "../Components/UploadAlerts.jsx";
import UploadListItem from "../Components/UploadListItem.jsx";

function AnnualUploadPage() {
  let [successfulUpdate, setSuccessfulUpdate] = useState(false);
  let [errorflag, setErrorflag] = useState(false);
  let [errorMessage, setErrorMessage] = useState("");
  let [uploadedFile, setUploadedFile] = useState(null);

  const onClose = () => {
    setErrorflag(false);
    setSuccessfulUpdate(false);
  };

  const updateUploadedFile = (file_id, original_filename) => {
    setSuccessfulUpdate(true);
    setErrorflag(false);
    setUploadedFile({
      file_id: file_id,
      original_filename: original_filename,
    });
  };

  const handleFileAccepted = (acceptedFiles) => {
    setErrorflag(false);
    setSuccessfulUpdate(false);

    if (acceptedFiles && acceptedFiles.length == 0) {
      setSuccessfulUpdate(false);
      setErrorflag(true);
      setErrorMessage(
        "Invalid file type, please upload .csv, .xlsx, or .xls files only"
      );
    } else {
      upload_file(acceptedFiles[0])
        .then((response) => {
          setSuccessfulUpdate(true);
          setErrorflag(false);
          setUploadedFile({
            file_id: response.data.file_id,
            original_filename: response.data.original_filename,
          });
        })
        .catch((error) => {
          console.log(error);
          setSuccessfulUpdate(false);
          setErrorflag(true);
          setErrorMessage(error.response.data.error);
        });
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
          onFilesAccepted={handleFileAccepted}
          maxFiles={uploadedFile ? 0 : 1}
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
        {uploadedFile && (
          <UploadListItem
            uploadedFile={uploadedFile}
            onClick={() => {
              setUploadedFile(null);
            }}
          />
        )}
        <RecentUploads
          updateUploadedFile={updateUploadedFile}
          rerender={uploadedFile}
        />
      </MyBox>
      <MyBox
        sx={{ display: "flex", justifyContent: "center" }}
        transition={{ duration: 1 }}
      >
        <CustomButton
          disabled={uploadedFile == null}
          title={"Generate report"}
          navigateTo={"/report/display"}
          state={{
            uploadedFiles: [uploadedFile],
          }}
        ></CustomButton>
      </MyBox>
    </>
  );
}

export default AnnualUploadPage;
