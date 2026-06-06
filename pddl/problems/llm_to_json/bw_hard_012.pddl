(define (problem bw_hard_012)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table f)
    (on_table a)
    (on_table c)
    (on e f)
    (on d e)
    (on b a)
    (clear d)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (and
      (on c d)
      (on b e)
    )
  )
)
