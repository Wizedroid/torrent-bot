# README


## Configuration

#### Movies

| parameter | Description                 | type    | required | default           |
|-----------|-----------------------------|---------|----------|-------------------|
| name      | Name of the movie           | String  | yes      | None              |
| max_size  | Max size in GB              | integer | no       | -1 (unlimited)    |
| year      | Year the movie was released | String  | no       | None              |
| res       | Resolution                  | Array   | no       | ["720p", "1080p"] |
| lang      | Movie Language              | String  | no       | None              |
| dir       | Destination directory       | String  | yes      | None              |