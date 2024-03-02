# ARIA-Hyp3 GUNW Submission by Frame

These notebooks illustrate and document how to generate large Hyp3 bulk submissions for a GUNW v3 product. The GUNW v3 (see details [here](https://github.com/ACCESS-Cloud-Based-InSAR/DockerizedTopsApp) on the GUNW specifications) is a spatially-fixed frame product with troposphere, ionosphere, and Solid Earth Tide correction layers. For submitting jobs, we rely on the fixed frame [enumeration](https://github.com/ACCESS-Cloud-Based-InSAR/s1-frame-enumerator) using spatially fixed frames derived from the ESA burst map (see more details about these frames [here](https://github.com/ACCESS-Cloud-Based-InSAR/s1-frame-generation)).

This repository is highly interactive. We will work on tighter version control if more additions are needed, but for the time-being, these notebooks illustrate how to use the libraries to do large scale enumeration


# Generate a full time series of GUNW v3 products

Currently, we are focused on submitting a time-series of GUNWs v3 over large spatial AOIs. 

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
+ Geojson files used to store SLC stacks and pairings from 1.


# Installation

Install the environment and the notebook kernel via:

```
mamba env update -f environment.yml
python -m ipykernel install --user --name aria_hyp3_env
```

# Usage

Go through the notebooks in order.

Update the [`enumeration_parameters.yml`](enumeration_parameters.yml) as needed for the enumeration.

# Checklist before Submitting Jobs

- [ ] Correct AWS account (We have three accounts: Tibet, Nisar, and ACCESS)
- [ ] Correct job type (INSAR_ISCE vs. INSAR_ISCE_TEST, usually former for large jobs)
- [ ] Weather model correct
    - [ ] HRRR for CONUS (this excludes AK! until we update RAiDER)
    - [ ] None everywhere else

# Notes

## Monitoring Jobs

Hyp3 puts all the jobs into a single queue and if there are multiple steps as is the case for our workflow, each successful step is put into the *back* of this queue. For our workflow there is the (1) topsapp step taking ~3 hours and (2) raider step taking approximately 20 minutes if correction applied and seconds if not. The raider step is even if a weather model is *NOT* applied, "doing nothing". It's important to note that you will *see failures* before *successes* because of this as transient errors will occur quickly, but if you submit say 20k jobs, you won't successfully complete jobs until all the 20k jobs do the first step and then complete the relatively quick second step.

When we print out `job` objects from `hyp3`, we see something like this:
```
986 HyP3 Jobs: 0 succeeded, 0 failed, 110 running, 876 pending.
```

Note the `running` will accumulate (depending on how many jobs are in the fleet).

## Controlling the Fleet Size via Hyp3

Spot market instances are cheaper but are vulnerable to random "terminations" - being shut down if there is not enough instances available for customers of the "on-demand" fleet. We have experts in Andrew Johnston and Joe Kennedy to guide us, but a lot of it is random.

To understand how hyp3 controls the number of instances, we have:

- Number of threads here: https://github.com/ASFHyP3/hyp3/blob/develop/job_spec/INSAR_ISCE.yml#L76
- Instance types and max VCPUs here: https://github.com/ASFHyP3/hyp3/blob/develop/.github/workflows/deploy-enterprise.yml#L63-L65
- Instance memory and vCPUs here: https://aws.amazon.com/ec2/instance-types/#compute-optimized

Note we have our threads (4) to be the same as the VCPUs with the maximum allowable memory for the lowest end instance (in our case `c6i.xlarge` has 4 VCPUs and 8 GiB of memory). As we go up the instance family, we can put multiple jobs in the same instance. Note, we are only *controlling VCPUs. Therefore we expect that our 10000 VCPUs (which is the configuration linked at the time of writing this) will be about 250 jobs able to run concurrently.

## Current Submission Workflow

We have experience getting 90-95% of jobs to run successfully -- transient errors may persist at this scale or some edge ISCE case. This has been good enough to generate time series. With on-demand instances, we can get close to that from the first run. With spot instances, we have reduced our fleet significantly, but have found as of this writing about 87% success. It's good to submit your jobs in a notebook, record the job names for monitoring, and then resubmit the failures. We have some scripts from Andrew Johnston to further analyze spot terminations from jobs that fail.
