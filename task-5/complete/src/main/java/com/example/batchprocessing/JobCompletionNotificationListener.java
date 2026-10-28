package com.example.batchprocessing;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobExecutionListener;
import org.springframework.batch.core.StepExecution;
import org.springframework.jdbc.core.DataClassRowMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicLong;

@Component
public class JobCompletionNotificationListener implements JobExecutionListener {

	private static final Logger log = LoggerFactory.getLogger(JobCompletionNotificationListener.class);

	private final JdbcTemplate jdbcTemplate;
	private final Counter batchJobFailures;
	private final AtomicLong lastRunRowsAdded = new AtomicLong(0);

	public JobCompletionNotificationListener(JdbcTemplate jdbcTemplate, MeterRegistry meterRegistry) {
		this.jdbcTemplate = jdbcTemplate;
		this.batchJobFailures = Counter.builder("batch_job_failures_total")
				.tag("application", "batch-processing")
				.register(meterRegistry);
		meterRegistry.gauge("batch_job_last_run_rows_added", lastRunRowsAdded, AtomicLong::get);
}

	@Override
	public void afterJob(JobExecution jobExecution) {
		if (jobExecution.getStatus() == BatchStatus.COMPLETED) {
			long rowsAdded = jobExecution.getStepExecutions().stream()
				.mapToLong(StepExecution::getWriteCount)
				.sum();
			lastRunRowsAdded.set(rowsAdded);

			log.info("!!! JOB FINISHED! Rows added: {}. Time to verify the results", rowsAdded);

			jdbcTemplate
				.query("SELECT productId, productSku, productName, productAmount, productData FROM products", new DataClassRowMapper<>(Product.class))
				.forEach(person -> log.info("Transformed <{}> in the database.", person));
	} else if (jobExecution.getStatus() == BatchStatus.FAILED) {
			batchJobFailures.increment();
			log.error("!!! JOB FAILED! Exit status: {}", jobExecution.getExitStatus());
		}
	}
}
