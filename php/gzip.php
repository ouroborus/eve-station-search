<?
  header("Content-Type: application/javascript");
  $headers = getallheaders();
  print("wantsGzip(");
  print((array_key_exists("Accept-Encoding",$headers) && strpos($headers["Accept-Encoding"],"gzip")!==false)?"true":"false");
  print(");\n");
?>
