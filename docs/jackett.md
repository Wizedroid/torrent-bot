# Jacket Notes

Based on [torznab](https://torznab.github.io/spec-1.3-draft/index.html) specification

## API

### Root Endpoint

```bash
export INDEX=all
http://127.0.0.1:9117/api/v2.0/indexers/${INDEX}/results/torznab
```

### Torznab API

Shows the available parameters for the indexer

```bash
export INDEX=all
export API_KEY=<replace_w_your_api_key>
http://127.0.0.1:9117/api/v2.0/indexers/${INDEX}/results/torznab?&t=caps&apikey=${API_KEY}
```

### Example Query
```bash
export INDEX=all
export API_KEY=<replace_w_your_api_key>
http://127.0.0.1:9117/api/v2.0/indexers/${INDEX}/results/torznab?t=${FUNCTION}&apikey=${API_KEY}&q=yellowjackets&ep=1&season=1
```

### Jackett API

http://127.0.0.1:9117/api/v2.0/indexers/all/results/?t=${FUNCTION}&apikey=${API_KEY}&query=${SEARCH_TERMS}