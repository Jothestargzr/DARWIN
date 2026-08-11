diff --git a/mojo/core/ipcz_driver/wrapped_platform_handle.cc b/mojo/core/ipcz_driver/wrapped_platform_handle.cc
index a2fab55..875e0d1 100644
--- a/mojo/core/ipcz_driver/wrapped_platform_handle.cc
+++ b/mojo/core/ipcz_driver/wrapped_platform_handle.cc
@@ -22,7 +22,14 @@
 
 #if BUILDFLAG(IS_MAC)
 #include <mach/mach.h>
+#if __has_include(<sys/fileport.h>)
 #include <sys/fileport.h>
+#else
+extern "C" {
+int fileport_makeport(int fd, mach_port_t *port);
+int fileport_makefd(mach_port_t port);
+}
+#endif
 #endif
 
 namespace mojo::core::ipcz_driver {
