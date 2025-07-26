import { RiDeleteBinFill } from "react-icons/ri";
import Avatar from "@mui/material/Avatar";
import { TbFileTypeXls } from "react-icons/tb";
import Paper from "@mui/material/Paper";
import { MyBox } from "../Components/MotionComponents";
function UploadListItem({ uploadedFile, onClick }) {
  return (
    <>
      <Paper
        elevation={2}
        sx={{
          display: "flex",
          width: "80%",
          padding: "1rem",
          margin: "1rem",
        }}
      >
        <MyBox sx={{ width: "15%", justifyItems: "center" }}>
          <Avatar sx={{ bgcolor: "green" }}>
            <TbFileTypeXls />
          </Avatar>
        </MyBox>
        <MyBox sx={{ flexGrow: 1, alignContent: "center" }}>
          {uploadedFile.original_filename}
        </MyBox>
        <MyBox sx={{ alignContent: "center" }}>
          <RiDeleteBinFill color="red" fontSize={"1.5rem"} onClick={onClick} />
        </MyBox>
      </Paper>
    </>
  );
}

export default UploadListItem;
