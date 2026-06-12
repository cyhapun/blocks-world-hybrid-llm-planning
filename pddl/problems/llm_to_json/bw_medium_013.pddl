(define (problem bw_medium_013)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on d a)
    (clear c)
    (clear d)
    (clear b)
    (handempty)
  )

  (:goal
    (on c d)
  )
)
