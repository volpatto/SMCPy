import logging

class VectorMCMCLogger:

    def __init__(self, name, debug=False):
        self._logger = logging.getLogger(__name__)
        sh = logging.StreamHandler()
        fmt = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        sh.setFormatter(fmt)
        self._logger.addHandler(sh)
        if debug:
            self._logger.setLevel(10)

    def _log_sample(self, inputs, log_likes, log_priors, iter_, proposed):
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('{:*^30}'.format(' iteration {} '.format(iter_)))
            self._logger.debug('proposed = {}'.format(proposed))
            self._logger.debug('inputs = {}'.format(inputs))
            self._logger.debug('log_likes = {}'.format(log_likes))
            self._logger.debug('log_priors = {}\n'.format(log_priors))

    def _log_acceptance(self, accpt_ratio, u):
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('acceptance ratio = {}'.format(accpt_ratio))
            self._logger.debug('u = {}'.format(u))
            self._logger.debug('accepted = {}'.format(accpt_ratio > u))

    def _log_cov(self, cov):
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('cov = {}'.format(cov))
