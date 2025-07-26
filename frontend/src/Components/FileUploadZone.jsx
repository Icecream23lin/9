import { useDropzone } from "react-dropzone";
import Paper from "@mui/material/Paper";
import { MyBox } from "./MotionComponents";
import ButtonBase from "@mui/material/ButtonBase";
import { PiBrowsers } from "react-icons/pi";
import { RiDragDropLine } from "react-icons/ri";

function FileUploadZone({ onFilesAccepted, maxFiles }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    maxFiles: maxFiles,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
    onDrop: (acceptedFiles) => {
      if (maxFiles != 0) {
        onFilesAccepted(acceptedFiles);
      }
    },
  });

  const { ref, ...rootProps } = getRootProps();

  return (
    <MyBox
      ref={ref}
      sx={{
        width: "100%",
        height: "70%",
        alignContent: "center",
        textAlign: "center",
        opacity: maxFiles == 0 ? 0.5 : 1,
        pointerEvents: maxFiles == 0 ? "none" : "auto",
      }}
    >
      <ButtonBase
        sx={{
          borderRadius: "2rem",
          width: "40%",
          height: "70%",
        }}
      >
        <Paper
          elevation={3}
          data-testid="dropzone"
          {...rootProps}
          sx={{
            alignContent: "center",
            borderRadius: "2rem",
            width: "100%",
            height: "100%",
          }}
        >
          <input {...getInputProps()} />
          {!isDragActive && (
            <>
              <MyBox sx={{ fontSize: "3rem" }}>
                <PiBrowsers color="#1976d2" />
                <RiDragDropLine color="#1976d2" />
              </MyBox>
              <MyBox sx={{ fontSize: "1rem" }}>
                <div>Upload files</div>
              </MyBox>
            </>
          )}
          {isDragActive && (
            <>
              <MyBox sx={{ fontSize: "3rem" }}>
                <RiDragDropLine color="#1976d2" />
              </MyBox>
              <MyBox sx={{ fontSize: "1rem" }}>
                <div>Drop files here</div>
              </MyBox>
            </>
          )}
        </Paper>
      </ButtonBase>
    </MyBox>
  );
}

export default FileUploadZone;
