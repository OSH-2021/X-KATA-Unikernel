package types

// Config for Build
type Config struct {
	// Args defines an array of commands to execute when the image is launched.
	Args []string
	
	// Boot
	Boot string

	// BuildDir
	BuildDir string

	// Dirs defines an array of directory locations to include into the image.
	Dirs []string

	// Files defines an array of file locations to include into the image.
	Files []string

	// Force
	Force bool

	// Kernel
	Kernel string

	// Program
	Program string

	// ProgramPath specifies the original path of the program to refer to on
	// attach/detach.
	ProgramPath string

	// RebootOnExit defines whether the image should automatically reboot
	// if an error/failure occurs.
	RebootOnExit bool

	// RunConfig
	RunConfig RunConfig

	// TargetRoot
	TargetRoot string

	// Version
	Version string

}


// Tag is used as property on creating instances
type Tag struct {
	// Key
	Key string `json:"key"`

	// Value
	Value string `json:"value"`
}

// RunConfig provides runtime details
type RunConfig struct {
	// CPUs specifies the number of CPU cores to use
	CPUs int

	// Imagename (FIXME)
	Imagename string

	// InstanceName
	InstanceName string

	// Memory configures the amount of memory to allocate to qemu (default
	// is 128 MiB). Optionally, a suffix of "M" or "G" can be used to
	// signify a value in megabytes or gigabytes respectively.
	Memory string

	// Background runs unikernel in background
	// use onprem instances commands to manage the unikernel
	Background bool

	// Ports specifies a list of port to expose.
	Ports []string

	// ShowErrors
	ShowErrors bool

}

// RuntimeConfig constructs runtime config
func RuntimeConfig(image string, ports []string, verbose bool) RunConfig {
	return RunConfig{Imagename: image, Ports: ports, Verbose: verbose, Memory: "2G", Accel: true}
}
