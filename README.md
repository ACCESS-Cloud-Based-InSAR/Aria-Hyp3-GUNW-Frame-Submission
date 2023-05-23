# ARIA-Hyp3 GUNW Submission by Frame

These notebooks illustrate and document how to generate large Hyp3 bulk submissions for a GUNW v3 product. The GUNW v3 (see details [here](https://github.com/ACCESS-Cloud-Based-InSAR/DockerizedTopsApp) on the GUNW specifications) is a spatially-fixed frame product with troposphere, ionosphere, and Solid Earth Tide correction layers. For submitting jobs, we rely on the fixed frame [enumeration](https://github.com/ACCESS-Cloud-Based-InSAR/s1-frame-enumerator) using spatially fixed frames derived from the ESA burst map (see more details about these frames [here](https://github.com/ACCESS-Cloud-Based-InSAR/s1-frame-generation)).


# Generate a full time series of GUNW v3 products

Currently, we are focused on reprocessing a full time-series of GUNWs v3. In future, we will include scenarios within this workflow for forward processing using existing v3 and v2 time-series.

The general workflow is:

1. Create a large AOI (this example will focus on coastal Continental US excluding Alaska)
2. Enumerate GUNWs for several temporal baselines
   + Use the [S1-Frame-Enumerator](https://github.com/ACCESS-Cloud-Based-InSAR/s1-frame-enumerator)
   + Deduplicate Submissions (due to S1 SLC availability)
   + Serialize the Submission Data
3. Submit Jobs to Hyp3 through the Rest API (in Batches)
   + Load local database
   + Check CMR for duplicates
4. Track and Resubmit Failed Jobs to Hyp3
   + Serialize submission data and delivery status

There are two types of data within this repository:

+ AOIs - large areas of interest and last processing date
+ Parquet files used for processing campaigns

# Usage



# Installation

# Contributing
