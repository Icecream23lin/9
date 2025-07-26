import Tooltip from "@mui/material/Tooltip";
import IconButton from "@mui/material/IconButton";
function CustomTooltip({ icon, title }) {
  return (
    <Tooltip title={title}>
      <IconButton>{icon}</IconButton>
    </Tooltip>
  );
}

export default CustomTooltip;
