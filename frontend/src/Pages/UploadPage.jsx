import { MyBox } from "../Components/MotionComponents";
import AnnualUploadPage from "./AnnualUploadPage";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import { useState } from "react";
import YoYUploadPage from "./YoYUploadPage";

function UploadPage() {
  const [value, setValue] = useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  const tabstyle = {
    color: "#1976d2",
    "&.Mui-selected": {
      color: "whitesmoke", // light blue or your brand color
      fontWeight: "bold",
    },
  };
  return (
    <>
      <MyBox sx={{ height: "100vh", width: "100vw", overflowX: "hidden" }}>
        <MyBox
          sx={{
            width: "100%",
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "rgb(0,0,0,0.3)",
            justifyItems: "center",
          }}
        >
          <Tabs value={value} onChange={handleChange}>
            <Tab label="Annual report" value={0} sx={tabstyle} />
            <Tab label="YoY Comparison" value={1} sx={tabstyle} />
          </Tabs>
        </MyBox>
        <MyBox
          key={value}
          sx={{ height: "80%" }}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.3 }}
        >
          {value == 0 && <AnnualUploadPage />}
          {value == 1 && <YoYUploadPage />}
        </MyBox>
      </MyBox>
    </>
  );
}

export default UploadPage;
