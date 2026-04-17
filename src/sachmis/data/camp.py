class FileManager:
    # INFO: from here files, move to new registry or manager?
    #
    def load_local_files(
        self,
        local_file_dir: Path | None = None,
        from_empty_status=False,
    ):
        """Update file registry with new files placed in folder"""
        config: SachmisConfig = get_config()

        # TASK: split in:
        # - load or update from .camp/files
        # - load from other folder (or recive directly list with paths)
        # Move files from local_file_dir to target_dir

        self._prepare_file_registry(from_empty_status)
        logger.info(f"Start loading files: {self.n_files=}")

        target_dir: Path = config.paths.file_dir
        local_file_dir: Path = local_file_dir or target_dir
        # TODO: what else when local==target?

        new_files: list[str] = [
            file.name
            for file in local_file_dir.glob("*")
            if file.is_file()
            # TODO: check for dublicated, especially from camp
        ]

        result: list[UploadFile] = []

        for file in new_files:
            # NEXT: call read, process move function file per file
            # TODO: keyword, at least current topic!
            if file in self.file_names:
                msg = f"Dublicated name for: {file=}, implement hash or compare size?"
                logger.warning(msg)
                continue
            # TODO: global_path: Path = PathGuard.unique(Path(file))
            # - slugify name, but store original
            # check with shmoodle
            new_file = UploadFile(local_path=Path(file))
            self.files.append(new_file)
            result.append(new_file)
            logger.info(f"Added {new_file=}")

        # MOVE: return list, caller prints

    def load_files_from_path(self, files: list[Path]) -> list[UploadFile]:
        config: SachmisConfig = get_config()

        # TASK: FolderScanner
        # - generic for any type
        # - setup for Files
        # - setup for Images
        confirmed_files: list[UploadFile] = []
        new_loaded_files: list[UploadFile] = []

        for file in files:
            if file.name in self.file_names:
                confirmed_files.append(self.file_by_name(file.name))
                logger.debug(f"Already loaded: {file.name=}")
            else:
                camp_file: Path = config.paths.file_dir / file.name
                shutil.copy(file, camp_file)
                forest_file = UploadFile(local_path=camp_file)
                self.files.append(forest_file)
                new_loaded_files.append(forest_file)
                logger.info(f"Attached to Forest: {file.name=}")

        logger.info(f"Prepared: {new_loaded_files=}")
        confirmed_files += new_loaded_files

        logger.info(f"Total: {confirmed_files=}")
        return confirmed_files
