#!/usr/bin/env bash

# Delete local data and model artifacts except for .gitkeep
find ./data -mindepth 1 ! -name '.gitkeep' -delete
find ./models -mindepth 1 ! -name '.gitkeep' -delete
