plugins { id("java-library") }
java { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
sourceSets { main { java.srcDir("ANDROIDX_SRC/arch/core/core-common/src/main/java") } }
dependencies { api(project(":shim-annotation")); api("org.jspecify:jspecify:1.0.0") }
