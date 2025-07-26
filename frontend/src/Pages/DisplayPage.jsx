import { MyBox } from "../Components/MotionComponents";
import { IoIosArrowBack } from "react-icons/io";
import { useNavigate, useLocation } from "react-router-dom";
import Button from "@mui/material/Button";
import { useEffect, useState } from "react";
import Loading from "../Components/Loading";
import { IoMdPhotos } from "react-icons/io";
import CustomTooltip from "../Components/CustomToolTip";
import {
  getAllVisualisation,
  getPdfUrl,
  getReport,
  getReportBatch,
} from "../services";
function DisplayPage() {
  const location = useLocation();

  const { uploadedFiles } = location.state || {};

  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [analysisId, setAnalysisId] = useState("");
  const [pdf, setPdf] = useState("");

  const handleNotification = (message) => {
    if (Notification.permission === "granted") {
      new Notification(message);
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          new Notification(message);
        }
      });
    }
  };

  const handleDownloadVisualisations = () => {
    getAllVisualisation(analysisId)
      .then((response) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (window.electronAPI) {
            window.electronAPI
              .invoke("download-dialog", {
                file_name: uploadedFiles[0].original_filename,
                file: reader.result,
              })
              .then((response) => {
                if (response) {
                  handleNotification("✅ Download successful");
                } else {
                  handleNotification("Download unsuccessful");
                }
              });
          } else {
            const link = document.createElement("a");
            link.href = URL.createObjectURL(response.data);
            link.download = `${uploadedFiles[0].original_filename}.zip`;
            link.click();
          }
        };
        reader.readAsArrayBuffer(response.data);
      })
      .catch((e) => {
        console.log(e);
      });
  };

  useEffect(() => {
    // get report
    let promise;
    if (uploadedFiles.length == 1) {
      promise = getReport(uploadedFiles[0].file_id);
    } else {
      promise = getReportBatch(uploadedFiles.map((f) => f.file_id));
    }
    promise
      .then((response) => {
        setPdf(response.data.download_url);
        setAnalysisId(response.data.analysis_id);
        setLoading(false);
        handleNotification("✅ Report Generated");
      })
      .catch((e) => {
        console.log(e);
        handleNotification("Report Generation failed, try again later");
        setLoading(false);
      });
  }, []);

  return (
    <>
      {loading && (
        <Loading
          message={
            <>
              Report is being generated :) <br />
              You will be notified once report is ready!
            </>
          }
        />
      )}
      {!loading && (
        <>
          <MyBox
            sx={{
              display: "flex",
              padding: "10%",
              width: "80%",
              paddingBottom: "2%",
              paddingTop: "2%",
            }}
          >
            <MyBox sx={{ flexGrow: 1 }}>
              <Button
                variant="contained"
                startIcon={<IoIosArrowBack />}
                onClick={() => {
                  navigate("/report");
                }}
                sx={{
                  borderRadius: "0.5rem",
                }}
              >
                new report
              </Button>
            </MyBox>

            <MyBox
              sx={{ verticalAlign: "center" }}
              onClick={handleDownloadVisualisations}
            >
              <CustomTooltip
                title={"Download Visualisations"}
                icon={
                  <>
                    <IoMdPhotos size={"1.5rem"} color="white" />
                  </>
                }
              ></CustomTooltip>
            </MyBox>
          </MyBox>
          <MyBox sx={{ width: "90%", height: "65%", padding: "5%" }}>
            <iframe
              src={getPdfUrl(pdf)}
              title={uploadedFiles[0].original_filename}
              width="100%"
              height="100%"
              style={{ border: "1px solid gray" }}
            />
          </MyBox>
        </>
      )}
    </>
  );
}

export default DisplayPage;
