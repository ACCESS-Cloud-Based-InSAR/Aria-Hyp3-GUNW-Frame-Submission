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

- [ ] Check you have the correct earthdata username! If you use a ~/.netrc, be careful! Use `access_cloud_based_insar` for as ops user.
- [ ] Correct AWS account for hyp3 endpoint: (We have three accounts: Tibet, Nisar, and ACCESS)
- [ ] Correct endpoint within account i.e. `https://hyp3-a19-jpl.asf.alaska.edu` (production) vs. `https://hyp3-a19-jpl-test.asf.alaska.edu` (test)
- [ ] Weather model correct
    - [ ] HRRR for CONUS (this excludes AK! until we update RAiDER)
    - [ ] None everywhere else

# Notes

## Monitoring Jobs

Hyp3 puts all the jobs into a single queue and if there are multiple steps as is the case for our workflow, each successful step is put into the *back* of this queue. For our workflow there are two steps: (1) topsapp step taking ~2.5 hours and (2) raider step taking approximately 20 minutes if correction is applied and seconds if not. The raider step is required even if a weather model is *NOT* applied, via "doing nothing". It's important to note that you will *see failures* before *successes* because of this queue structure: transient errors will pile up, but if you submit say 20k jobs and you are allowing 1k jobs to run concurrently, you won't see successfully completed jobs until all the 20k jobs do the first step and then complete the second step.

When we print out `job` objects from `hyp3`, we see something like this:
```
986 HyP3 Jobs: 0 succeeded, 0 failed, 110 running, 876 pending.
```

Note the `running` will accumulate (depending on how many jobs can be run in parallel in the fleet).

## Deployment Notes: spot market, fleet size, instance families, etc.

Hyp3 is a very slim wrapper around many highly scalable AWS services. Scaling the best priced option is nuanced and that is roughly what we now discuss. 

The biggest expense for cloud compute is ec2 instances. You can rent instances "on demand" or you can pay a fraction of the cost on the "spot market" if you allow for random terminations of your work. A lot of "knowledge" about the spot market is anecdotal and their are strategies to mitigating spot market terminations (reducing the length of time for a given job, diversifying instances, and allowing for retries). Hyp3 retries a job 3 times automatically (believe this is a feature within AWS Batch and the services they already use). We note that with our extremely long running step (the topsApp ISCE2 step), our instances are highly vulernable to terminations and we have to be mindful of this. We have "diversified" instances in that we allow for numerous instances within an instance families so that if there is a shortage of a given instance we can easily move to another (possibly more expensive one). However, more expensive instances typically can fit multiple jobs and therefore the actual cost increase is negligible. If we can fit 2 jobs into an instance that is approximately twice as much, then we are in the clear. This "diversification" is indicated [here](https://github.com/ASFHyP3/hyp3/blob/develop/.github/workflows/deploy-enterprise.yml#L46). We can use `c6id.xlarge` for 1 topsapp job. Note the `c6id` are compute optimized with a 230+GB SSD attached (so we don't need to purchase extra disk). Many of instance classes have this `d` to indicate default attached SSD disk. As we go up the instance family, memory/disk/VCPUs all double.

To understand how hyp3 controls how many "jobs" can be fit into a given instances, we have:

- Number of threads used for single job here which is 4: https://github.com/ASFHyP3/hyp3/blob/develop/job_spec/INSAR_ISCE.yml#L76
- Amount of memory used for single job here in MBs (7.5 GiB): https://github.com/ASFHyP3/hyp3/blob/develop/job_spec/INSAR_ISCE.yml#L95
- Instance types and max VCPUs in hyp3 deployment: https://github.com/ASFHyP3/hyp3/blob/develop/.github/workflows/deploy-enterprise.yml#L63-L65
- Instance memory and VCPUs available for compute optimized family: https://aws.amazon.com/ec2/instance-types/#compute-optimized

Note we want the threads used for the plugin (4 as indicated above) to be the same as the VCPUs. We also want the maximum allowable memory for the lowest instance in the family (in our case `c6id.xlarge` which has 8 GiB of memory). As we go up the instance family, we put multiple jobs in the same instance as the memory constrains the an individual job. Again, memory/disk/VCPUs all double as we go up the instance chain. Therefore, `cid.2xlarge` has double the amount of memory/disk/VCPU as `cid.xlarge` and therefore can fit two jobs. For hyp3 deployment, the memory is what is used to dictate the number of jobs on the lowest instance and will be used to deterimine how jobs are fit into the higher end instances in the family.

To understand the number of concurrent jobs in a given hyp3 deployment, we divide the VCPUs available (determined in the deployment) and divide by the VCPUs/threads used in a job. Say we have 1000 VCPUs in the deployment and 1 job uses 4 VCPUs, then we expect 250 jobs to run concurrently.

Suppose we wish to explore a different instance family like the "memory-optimized" R-family. Then, as noted above, the constratint for hyp3 deployment is the memory in the job spec and we would ensure that the lowest instance we consider is maximally used so that as we go up the instance family, we can fit multiple jobs as before. 

## Some notes on the the Current Submission Workflow

We have experience getting 90-95% of jobs to run successfully -- transient errors may persist at this scale or some edge ISCE case. This has been good enough to generate time series. With on-demand instances, we can get close to that from the first run. With spot instances, we have reduced our fleet significantly, but have found as of this writing about 87% success. It's good to submit your jobs in a notebook, record the job names for monitoring, and then resubmit the failures. We have some scripts from Andrew Johnston to further analyze spot terminations from jobs that fail.

## Catching up AOIs

Currently deduplication is a bottle neck as we individually check each product within the archive. Therefore, if there is a large AOI, it's best to use `valid_date_range` to reduce the size of a stack and then enumerate that. For example, if the last GUNW over an AOI has some reference date, use a few months before that for the entire AOI to present day and that should allow you to enumerate the AOI effectively without having to de-duplicate the AOI over a time span that was previously enumerated.
