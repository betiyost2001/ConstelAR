import { AppBar, Toolbar, Typography } from "@mui/material";

export default function Header() {
  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          ArgentinaSpace — Air Quality (MVP)
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
