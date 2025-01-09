# Image analysis with CLIP model

This is a project to pull together and end-to-end image analysis API using text-image
embeddings. The intent is to build in several phases:

1. Build a basic API to upload and download images including metadata
1. Integrate pre-trained CLIP models to save embeddings for images at ingestion
1. Build out search functionality to allow image search in natural language and
   metadata filters
1. Test training of a custom CLIP-style model including image and text encoders
   and the overarching projection layers

At some point it may also require a basic front-end to demonstrate the API functionality.
